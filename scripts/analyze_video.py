#!/usr/bin/env python3
"""
Video Analysis - Intent-driven analysis using frame descriptions and transcript.

Two-stage pipeline:
1. Frame description: Extract visual details from each frame (intent-aware)
2. Video analysis: Synthesize frames + transcript into intent-focused analysis

Validation features:
- Vision manifest verification (audit trail of which frames were viewed)
- Frame count validation (input vs output)
- Auto-retry for missing frames
- Quality checks for sparse descriptions
- Additional frame extraction on request
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

from transcript_utils import (
    parse_srt,
    parse_frame_timestamp,
    format_timestamp_display,
    get_transcript_at_timestamp,
    get_intent_aligned_timestamps,
    SRTBlock,
)


# Hard cap on how many frames the describer ever runs over. Prevents a
# blown-up frames/ directory (e.g. 200+ files from a 30-min video) from
# turning into 200 vision calls. The intent-aligned selector picks the
# most relevant N timestamps; only those are described.
_MAX_DESCRIBE_FRAMES_DEFAULT = 20


def _pick_frames_by_intent(
    frame_files: list[Path],
    transcript_srt: str,
    intent: str,
    max_frames: int,
) -> list[Path]:
    """Filter frame_files down to `max_frames` intent-aligned picks.

    Uses transcript_utils.get_intent_aligned_timestamps to score each
    transcript line on (visual-reference × intent-alignment) and returns
    the frame nearest each winning timestamp. Falls back to the unfiltered
    list if no intent is given or scoring returns nothing useful."""
    if not intent or not intent.strip() or not frame_files:
        return frame_files[:max_frames] if len(frame_files) > max_frames else frame_files

    picks = get_intent_aligned_timestamps(transcript_srt, intent, max_frames=max_frames)
    if not picks:
        return frame_files[:max_frames] if len(frame_files) > max_frames else frame_files

    frames_by_ts = sorted(
        ((parse_frame_timestamp(f.name), f) for f in frame_files),
        key=lambda x: x[0],
    )
    if not frames_by_ts:
        return []

    chosen: list[Path] = []
    seen: set[Path] = set()
    for pick in picks:
        target = pick["timestamp_seconds"]
        _, nearest = min(frames_by_ts, key=lambda pair: abs(pair[0] - target))
        if nearest not in seen:
            seen.add(nearest)
            chosen.append(nearest)
    return chosen

# Subagents (frame-describer, video-analyzer) live at `<repo>/.claude/agents/`.
# `claude --print --agent <name>` finds them via the CWD's `.claude/` directory,
# so we must invoke it from the repo root. This path resolves to:
#   scripts/analyze_video.py → parent x 2 → repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent

# Resolve the `claude` binary — it may not be on PATH when invoked from the bot.
_CLAUDE_BIN = shutil.which("claude") or str(Path.home() / ".local/bin/claude")


def _subprocess_env() -> dict:
    """Environment for `claude` subprocess calls.

    The claude CLI is a Node wrapper: it needs `node` on PATH, and the MCP
    servers it may spawn (uvx, npx) need their own binaries too. When this
    module is invoked from bot.py running under launchd, the inherited PATH
    is minimal (`/usr/bin:/bin:/usr/sbin:/sbin`) and misses Homebrew +
    `~/.local/bin`, so the child exits with FileNotFoundError mid-run.
    Prepend the common install prefixes explicitly so the child resolves
    every tool the claude CLI expects."""
    env = os.environ.copy()
    home = Path.home()
    extras = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
        str(home / ".local/bin"),
    ]
    existing = env.get("PATH", "")
    existing_parts = existing.split(":") if existing else []
    merged = extras + [p for p in existing_parts if p not in extras]
    env["PATH"] = ":".join(merged)
    return env


def validate_frame_descriptions(frame_files: list[Path], frame_data: dict) -> list[str]:
    """Validate frame descriptions completeness.

    Args:
        frame_files: List of input frame file paths
        frame_data: Parsed frame descriptions from agent

    Returns:
        List of warning messages (empty if all valid)
    """
    warnings = []

    # Check manifest exists
    validation = frame_data.get("validation", {})
    if not validation:
        warnings.append("No validation manifest in agent output")
        return warnings

    # Count check
    input_count = len(frame_files)
    output_count = len(frame_data.get("frames", []))
    received = validation.get("frames_received", 0)
    described = validation.get("frames_described", 0)

    if input_count != output_count:
        warnings.append(f"Frame count mismatch: {input_count} input, {output_count} output")

    if received != described:
        warnings.append(f"Agent received {received} but described {described}")

    # Filename check
    input_names = {f.name for f in frame_files}
    output_names = {f["filename"] for f in frame_data.get("frames", [])}
    missing = input_names - output_names
    if missing:
        warnings.append(f"Missing descriptions for: {missing}")

    # Vision audit
    viewed = set(validation.get("frames_viewed_with_vision", []))
    not_viewed = input_names - viewed
    if not_viewed:
        warnings.append(f"Frames NOT viewed with vision: {not_viewed}")

    # Skipped check
    skipped = validation.get("frames_skipped", [])
    if skipped:
        warnings.append(f"Agent skipped frames: {skipped}")

    # Quality check - sparse descriptions
    for frame in frame_data.get("frames", []):
        desc = frame.get("description", "")
        if len(desc) < 20:
            warnings.append(f"Sparse description ({len(desc)} chars): {frame.get('filename')}")

        # Check for empty visual elements
        visual = frame.get("visual_elements", {})
        if all(not v for v in visual.values()):
            warnings.append(f"No visual elements captured for {frame.get('filename')}")

    return warnings


def extract_frame_at_timestamp(video_path: Path, timestamp: int, output_dir: Path) -> Optional[Path]:
    """Extract a single frame at specific timestamp using ffmpeg.

    Args:
        video_path: Path to video file
        timestamp: Timestamp in seconds
        output_dir: Directory to save extracted frame

    Returns:
        Path to extracted frame, or None if extraction failed
    """
    mins = timestamp // 60
    secs = timestamp % 60
    output_file = output_dir / f"frame_extra_{mins:02d}m{secs:02d}s.jpg"

    result = subprocess.run([
        "ffmpeg", "-y", "-ss", str(timestamp),
        "-i", str(video_path),
        "-frames:v", "1", "-q:v", "2",
        str(output_file)
    ], capture_output=True)

    if result.returncode == 0 and output_file.exists():
        return output_file
    return None


def _run_describer_chunk(
    chunk_frames: list[dict],
    intent: str,
    metadata: dict,
    chunk_idx: int,
    chunk_total: int,
) -> dict:
    """Run one frame-describer subprocess on a chunk of frames.

    Returns parsed JSON (frames + validation). Raises on non-zero exit or
    unparseable output — caller treats those as chunk-level failures.
    """
    prompt = f"""## User Intent
{intent}

## Video Information
Title: {metadata.get('title', 'Unknown')}
Channel: {metadata.get('channel', 'Unknown')}
Description: {metadata.get('description', 'N/A')[:500]}

## Frames to Analyze ({len(chunk_frames)} in this chunk, part {chunk_idx}/{chunk_total})

Analyze each frame below. Use the Read tool to view each image file.
IMPORTANT: You must use Read on ALL {len(chunk_frames)} frames and report them in frames_viewed_with_vision.

"""
    for f in chunk_frames:
        prompt += f"""### Frame: {f['filename']}
- Path: {f['path']}
- Timestamp: {f['timestamp_formatted']}
- Transcript context: "{f['transcript_context'][:200]}..."

"""

    prompt += """
Return your analysis as JSON following the exact format from your instructions.
Include the validation block with frames_received, frames_described, and frames_viewed_with_vision."""

    try:
        result = subprocess.run(
            [_CLAUDE_BIN, "--print", "--agent", "frame-describer", "--allowedTools", "Read"],
            input=prompt,
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            env=_subprocess_env(),
            timeout=240,  # 4 min hard ceiling per chunk — prevents hung subprocesses blowing the Bash budget
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"chunk {chunk_idx} timed out after 240s")

    if result.returncode != 0:
        raise RuntimeError(f"subprocess exit {result.returncode}: {result.stderr[:300]}")

    output = result.stdout.strip()
    json_match = re.search(r'\{[\s\S]*\}', output)
    if not json_match:
        raise RuntimeError("no JSON found in describer output")
    return json.loads(json_match.group())


def describe_frames_with_agent(
    frames_dir: Path,
    transcript_srt: str,
    intent: str,
    metadata: dict,
    frame_subset: Optional[list[Path]] = None,
    video_path: Optional[Path] = None,
    max_retries: int = 2
) -> dict:
    """Stage 1: Generate intent-aware frame descriptions with validation.

    Args:
        frames_dir: Path to frames directory
        transcript_srt: SRT transcript content
        intent: User's analysis intent
        metadata: Video metadata dict
        frame_subset: Optional subset of frames to analyze (for retries)
        video_path: Path to video file (for extracting additional frames)
        max_retries: Maximum retry attempts for missing frames

    Returns:
        Dict with frame descriptions (frames_descriptions.json structure)
    """
    # Get frame files to analyze
    if frame_subset:
        frame_files = sorted(frame_subset)
    else:
        all_frames = sorted(frames_dir.glob("frame_*.jpg"))
        max_frames = int(os.environ.get("YTF_MAX_DESCRIBE_FRAMES", _MAX_DESCRIBE_FRAMES_DEFAULT))
        if len(all_frames) > max_frames:
            frame_files = _pick_frames_by_intent(all_frames, transcript_srt, intent, max_frames)
            print(
                f"  Capped describer input: {len(all_frames)} extracted → "
                f"{len(frame_files)} intent-aligned picks (cap={max_frames})"
            )
        else:
            frame_files = all_frames

    if not frame_files:
        return {"error": "No frames found", "frames": [], "validation": {}}

    # Parse transcript for context
    srt_blocks = parse_srt(transcript_srt)

    # Build frame info with context
    frames_info = []
    for frame_path in frame_files:
        timestamp = parse_frame_timestamp(frame_path.name)
        context = get_transcript_at_timestamp(srt_blocks, timestamp, window=10)
        frames_info.append({
            "path": str(frame_path),
            "filename": frame_path.name,
            "timestamp_seconds": timestamp,
            "timestamp_formatted": format_timestamp_display(timestamp),
            "transcript_context": context
        })

    # Chunk frames across parallel subagents. Each subprocess spins up a full
    # Claude Code session, so a single call describing 100+ frames serialises
    # every Read+vision turn and stalls for 10+ min. Splitting into N chunks
    # run concurrently cuts wall-clock ~Nx (minus the fixed bootstrap cost).
    chunk_size = int(os.environ.get("YTF_FRAME_CHUNK_SIZE", "20"))
    max_workers = int(os.environ.get("YTF_FRAME_WORKERS", "4"))
    chunks = [frames_info[i:i + chunk_size] for i in range(0, len(frames_info), chunk_size)]
    effective_workers = min(max_workers, len(chunks))

    print(
        f"  Analyzing {len(frame_files)} frames across {len(chunks)} chunk(s) "
        f"(≤{chunk_size} frames each, {effective_workers} parallel)..."
    )

    merged_frames: list[dict] = []
    merged_viewed: list[str] = []
    merged_skipped: list[str] = []
    merged_requests: list[dict] = []
    chunk_errors: list[str] = []

    with ThreadPoolExecutor(max_workers=effective_workers) as pool:
        futures = {
            pool.submit(_run_describer_chunk, chunk, intent, metadata, idx + 1, len(chunks)): idx
            for idx, chunk in enumerate(chunks)
        }
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                chunk_data = fut.result()
            except Exception as e:
                chunk_errors.append(f"chunk {idx + 1}: {e}")
                continue
            merged_frames.extend(chunk_data.get("frames", []))
            v = chunk_data.get("validation", {})
            merged_viewed.extend(v.get("frames_viewed_with_vision", []))
            merged_skipped.extend(v.get("frames_skipped", []))
            merged_requests.extend(v.get("request_additional_frames", []))

    frame_data = {
        "frames": merged_frames,
        "validation": {
            "frames_received": len(frame_files),
            "frames_described": len(merged_frames),
            "frames_viewed_with_vision": merged_viewed,
            "frames_skipped": merged_skipped,
            "request_additional_frames": merged_requests,
            "chunks": len(chunks),
            "chunk_errors": chunk_errors,
        },
    }

    if chunk_errors:
        for err in chunk_errors:
            print(f"  Warning: {err}")

    # Validate frame descriptions
    warnings = validate_frame_descriptions(frame_files, frame_data)
    for w in warnings:
        print(f"  Warning: {w}")

    # AUTO-RETRY: Re-run on missing frames
    validation = frame_data.get("validation", {})
    viewed = set(validation.get("frames_viewed_with_vision", []))
    input_names = {f.name for f in frame_files}
    missing = input_names - viewed

    if missing and max_retries > 0:
        print(f"  Auto-retry: {len(missing)} frames need vision analysis...")
        missing_files = [f for f in frame_files if f.name in missing]
        retry_data = describe_frames_with_agent(
            frames_dir, transcript_srt, intent, metadata,
            frame_subset=missing_files,
            video_path=video_path,
            max_retries=max_retries - 1
        )
        # Merge results
        frame_data["frames"].extend(retry_data.get("frames", []))
        if "validation" not in frame_data:
            frame_data["validation"] = {}
        frame_data["validation"]["retried_frames"] = list(missing)

    # Handle additional frame requests from agent
    requests = validation.get("request_additional_frames", [])
    if requests and video_path and video_path.exists():
        print(f"  Extracting {len(requests)} additional frames requested by agent...")
        new_frames = []
        for req in requests:
            ts = req.get("timestamp_seconds", 0)
            reason = req.get("reason", "")
            print(f"    - {ts}s: {reason}")
            new_frame = extract_frame_at_timestamp(video_path, ts, frames_dir)
            if new_frame:
                new_frames.append(new_frame)

        if new_frames:
            # Describe newly extracted frames
            extra_data = describe_frames_with_agent(
                frames_dir, transcript_srt, intent, metadata,
                frame_subset=new_frames,
                video_path=None,  # Don't recurse further
                max_retries=0
            )
            frame_data["frames"].extend(extra_data.get("frames", []))
            if "validation" not in frame_data:
                frame_data["validation"] = {}
            frame_data["validation"]["extra_frames_added"] = [f.name for f in new_frames]

    # Add metadata
    frame_data["intent"] = intent
    frame_data["generated_at"] = datetime.utcnow().isoformat() + "Z"

    return frame_data


def parse_analyzer_output(output: str) -> dict:
    """Parse video-analyzer output, handling both JSON and plain markdown.

    Args:
        output: Raw output from video-analyzer agent

    Returns:
        Dict with 'analysis_markdown' and optional 'request_additional_frames'
    """
    output = output.strip()

    # Try to parse as JSON first
    try:
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            data = json.loads(json_match.group())
            if "analysis_markdown" in data:
                return data
    except json.JSONDecodeError:
        pass

    # JSON parsing failed (often because the model wrote unescaped " inside a
    # JSON string value). Try to manually extract `analysis_markdown` by finding
    # the text between `"analysis_markdown": "` and the next `",\n` that precedes
    # a top-level JSON key (or end of object). This handles the common case where
    # the JSON is structurally valid except for literal quotes in the value.
    start_marker = '"analysis_markdown": "'
    end_markers = ['",\n\n  "request_additional_frames"', '",\n  "request_additional_frames"',
                   '"\n}', '"\n}']
    if start_marker in output:
        start = output.index(start_marker) + len(start_marker)
        for em in end_markers:
            if em in output[start:]:
                raw_val = output[start: output.index(em, start)]
                # Unescape standard JSON escapes; leave literal quotes as-is
                md = raw_val.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\').replace('\\"', '"')
                result: dict = {"analysis_markdown": md, "request_additional_frames": []}
                # Also try to extract answer
                answer_m = re.search(r'"answer":\s*"((?:[^"\\]|\\.)*)"', output)
                if answer_m:
                    result["answer"] = answer_m.group(1).replace('\\n', '\n').replace('\\"', '"')
                return result

    # Fall back to treating entire output as markdown
    return {"analysis_markdown": output, "request_additional_frames": []}


def analyze_video_with_agent(
    output_dir: Path,
    intent: str,
    regenerate_frames: bool = True
) -> tuple[str, dict]:
    """Run full analysis pipeline on a video output directory.

    Args:
        output_dir: Path to video output directory (e.g., out/250201-ytb-slug/)
        intent: User's analysis intent
        regenerate_frames: If True, regenerate frame descriptions even if they exist

    Returns:
        Tuple of (analysis_md, frames_descriptions)
    """
    output_dir = Path(output_dir)

    # Load required files
    metadata_path = output_dir / "metadata.json"
    transcript_path = output_dir / "transcript.srt"
    frames_dir = output_dir / "frames"
    frames_desc_path = output_dir / "frames_descriptions.json"
    analysis_path = output_dir / "analysis.md"
    video_path = output_dir / "video.mp4"

    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found in {output_dir}")

    metadata = json.loads(metadata_path.read_text())

    transcript_srt = ""
    if transcript_path.exists():
        transcript_srt = transcript_path.read_text()
    else:
        # Try plain text
        txt_path = output_dir / "transcript.txt"
        if txt_path.exists():
            transcript_srt = txt_path.read_text()

    # Full resume: if analysis.md already exists for THIS intent, skip both
    # stages. This is the cheap path when a previous run was /stop'd mid-way
    # and Lukas re-invokes with the same intent — no re-describing, no
    # re-synthesis, just hand back what's on disk.
    if analysis_path.exists() and analysis_path.stat().st_size > 0:
        existing_intent = ""
        if frames_desc_path.exists():
            try:
                existing_intent = (json.loads(frames_desc_path.read_text()).get("intent") or "")
            except Exception:
                pass
        if existing_intent.strip() == (intent or "").strip():
            print(f"  analysis.md already present for intent={intent!r}; skipping both stages")
            frames_data = (
                json.loads(frames_desc_path.read_text())
                if frames_desc_path.exists() else {"frames": [], "intent": intent, "validation": {}}
            )
            return analysis_path.read_text(), frames_data

    # Stage 1: Frame descriptions (intent-aware, so regenerate by default)
    print("Stage 1: Generating intent-aware frame descriptions...")

    # Stage-1 resume: if a prior run already produced frames_descriptions.json
    # for this exact intent, skip the vision calls entirely.
    prior_descriptions: Optional[dict] = None
    if frames_desc_path.exists() and frames_desc_path.stat().st_size > 0:
        try:
            prior = json.loads(frames_desc_path.read_text())
            if (
                isinstance(prior, dict)
                and (prior.get("intent") or "").strip() == (intent or "").strip()
                and prior.get("frames")
            ):
                prior_descriptions = prior
        except Exception:
            prior_descriptions = None

    if prior_descriptions is not None:
        print(
            f"  Reusing {len(prior_descriptions.get('frames', []))} cached "
            f"frame descriptions from frames_descriptions.json"
        )
        frames_data = prior_descriptions
    elif frames_dir.exists() and list(frames_dir.glob("frame_*.jpg")):
        frames_data = describe_frames_with_agent(
            frames_dir, transcript_srt, intent, metadata,
            video_path=video_path if video_path.exists() else None
        )
        frames_data["intent"] = intent  # tag for resume check next time

        # Save frame descriptions
        frames_desc_path.write_text(
            json.dumps(frames_data, indent=2, ensure_ascii=False)
        )
        print(f"  Saved: {frames_desc_path.name}")
    else:
        print("  No frames found, skipping frame analysis")
        frames_data = {"frames": [], "intent": intent, "validation": {}}

    # Stage 2: Video analysis with frame request loop
    print("Stage 2: Synthesizing video analysis...")

    max_frame_requests = 2  # Prevent infinite loops
    analysis_md = ""
    answer = ""

    for iteration in range(max_frame_requests + 1):
        if iteration > 0:
            print(f"  Re-analyzing with additional frames (iteration {iteration + 1})...")

        # Build prompt for video-analyzer agent
        frames_json = json.dumps(frames_data.get("frames", []), indent=2)

        prompt = f"""## User Intent
{intent}

## Video Metadata
{json.dumps(metadata, indent=2)}

## Frame Descriptions
{frames_json}

## Full Transcript
{transcript_srt}

Synthesize this information into a comprehensive analysis that addresses the user's intent.
Return as JSON with three fields:
- `answer`: 1-2 sentences directly answering the intent (the headline)
- `analysis_markdown`: the full markdown analysis
- `request_additional_frames`: optional list of timestamps where a frame is missing"""

        try:
            result = subprocess.run(
                [_CLAUDE_BIN, "--print", "--agent", "video-analyzer", "--allowedTools", "WebSearch"],
                input=prompt,
                capture_output=True,
                text=True,
                cwd=str(_REPO_ROOT),
                env=_subprocess_env(),
                timeout=300,  # 5 min hard ceiling for synthesis
            )
        except subprocess.TimeoutExpired:
            print("Warning: Video analyzer timed out after 300s")
            analysis_md = "# Analysis Failed\n\nVideo analyzer subprocess timed out."
            break

        if result.returncode != 0:
            print(f"Warning: Video analyzer agent failed: {result.stderr}")
            analysis_md = f"# Analysis Failed\n\nError: {result.stderr}"
            break

        # Parse output
        parsed = parse_analyzer_output(result.stdout)
        analysis_md = parsed.get("analysis_markdown", result.stdout.strip())
        # Only overwrite `answer` if the agent produced one this iteration —
        # a later iteration with no answer shouldn't blank out an earlier one.
        if parsed.get("answer"):
            answer = parsed["answer"].strip()

        # Check for additional frame requests
        frame_requests = parsed.get("request_additional_frames", [])
        if not frame_requests or iteration == max_frame_requests:
            break

        # Extract and describe requested frames
        if video_path.exists():
            print(f"  Video analyzer requested {len(frame_requests)} additional frames...")
            new_frames = []
            for req in frame_requests:
                ts = req.get("timestamp_seconds", 0)
                reason = req.get("reason", "")
                print(f"    - {ts}s: {reason}")
                new_frame = extract_frame_at_timestamp(video_path, ts, frames_dir)
                if new_frame:
                    new_frames.append(new_frame)

            if new_frames:
                # Describe newly extracted frames
                extra_data = describe_frames_with_agent(
                    frames_dir, transcript_srt, intent, metadata,
                    frame_subset=new_frames,
                    video_path=None,
                    max_retries=0
                )
                frames_data["frames"].extend(extra_data.get("frames", []))

                # Update validation
                if "validation" not in frames_data:
                    frames_data["validation"] = {}
                existing_extra = frames_data["validation"].get("analyzer_requested_frames", [])
                frames_data["validation"]["analyzer_requested_frames"] = (
                    existing_extra + [f.name for f in new_frames]
                )

                # Save updated frame descriptions
                frames_desc_path.write_text(
                    json.dumps(frames_data, indent=2, ensure_ascii=False)
                )
        else:
            print("  Cannot extract frames: video.mp4 not found")
            break

    # Save analysis
    analysis_path = output_dir / "analysis.md"
    analysis_path.write_text(analysis_md)
    print(f"  Saved: {analysis_path.name}")

    # Render the HTML page (single-file, shareable).
    try:
        from render_html import render as render_html
        html_path = render_html(output_dir, answer=answer or None)
        print(f"  Saved: {html_path.name}")
        public_url = _public_url_for(output_dir)
        if public_url:
            print(f"  Share: {public_url}")
    except Exception as e:
        # Don't fail the whole run if the renderer hiccups — analysis.md is already saved.
        print(f"  Warning: HTML render failed: {e}")

    return analysis_md, frames_data


def _public_url_for(output_dir: Path) -> str:
    """Build a shareable URL if you host the output behind a token gate.

    Set ASK_YT_PUBLIC_URL to the base of wherever you serve these pages
    (e.g. https://example.com). Returns "" if it isn't set or the page has
    no .share_token — in which case the local file path is the output.
    """
    base = os.environ.get("ASK_YT_PUBLIC_URL", "").rstrip("/")
    token_file = output_dir / ".share_token"
    if not base or not token_file.exists():
        return ""
    token = token_file.read_text().strip()
    return f"{base}/v/{output_dir.name}-{token}/"


def main():
    """CLI entry point for standalone analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze a downloaded YouTube video with intent-driven frame analysis"
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Path to video output directory (e.g., out/250201-ytb-my-video/)"
    )
    parser.add_argument(
        "--intent", "-i",
        type=str,
        help="Analysis intent (what you want to understand from the video)"
    )

    args = parser.parse_args()

    if not args.output_dir.exists():
        print(f"Error: Directory not found: {args.output_dir}")
        sys.exit(1)

    # Get intent interactively if not provided
    intent = args.intent
    if not intent:
        print("What would you like to analyze in this video?")
        print("Examples:")
        print("  - 'Extract key product demos and UI patterns'")
        print("  - 'Summarize the main arguments and evidence'")
        print("  - 'Identify all tools and technologies mentioned'")
        print()
        intent = input("Intent: ").strip()

        if not intent:
            print("Error: Intent is required")
            sys.exit(1)

    print(f"\nAnalyzing: {args.output_dir}")
    print(f"Intent: {intent}\n")

    analysis_md, frames_data = analyze_video_with_agent(args.output_dir, intent)

    print("\n" + "=" * 50)
    print("Analysis complete!")
    print(f"Output: {args.output_dir}")
    print("\nGenerated files:")
    print(f"  - frames_descriptions.json ({len(frames_data.get('frames', []))} frames)")
    print(f"  - analysis.md")


if __name__ == "__main__":
    main()
