#!/usr/bin/env python3
"""
Transcript utilities - parsing, querying, and frame correlation.

This is the single source of truth for all transcript/SRT operations.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union

_CLAUDE_BIN = shutil.which("claude") or str(Path.home() / ".local/bin/claude")

from config import KEY_TIMESTAMP_WINDOW


@dataclass
class SRTBlock:
    """A single SRT subtitle block."""
    index: int
    start_seconds: float
    end_seconds: float
    text: str


def parse_srt_timestamp(ts: str) -> float:
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
    # Handle both comma and period as decimal separator
    ts = ts.replace(',', '.')
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)


def format_timestamp_display(seconds: Union[int, float]) -> str:
    """Format seconds as MM:SS for display in analysis."""
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def format_timestamp_filename(seconds: Union[int, float]) -> str:
    """Format seconds as HHhMMmSSs for filenames."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}h{minutes:02d}m{secs:02d}s"
    return f"{minutes:02d}m{secs:02d}s"


def parse_frame_timestamp(filename: str) -> int:
    """Extract timestamp in seconds from frame filename.

    Args:
        filename: Frame filename like 'frame_0001_00m16s.jpg' or 'frame_0001_01h05m30s.jpg'

    Returns:
        Timestamp in seconds
    """
    # Try HHhMMmSSs format first
    match = re.search(r'(\d+)h(\d+)m(\d+)s', filename)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        return hours * 3600 + minutes * 60 + seconds

    # Fall back to MMmSSs format
    match = re.search(r'(\d+)m(\d+)s', filename)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes * 60 + seconds

    return 0


# Keep old name as alias for backwards compatibility during transition
parse_timestamp = parse_srt_timestamp


def parse_srt(srt_content: str) -> list[SRTBlock]:
    """Parse SRT content into structured blocks."""
    blocks = []
    current_block = []

    for line in srt_content.split('\n'):
        line = line.strip()
        if not line:
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    result = []
    for block in blocks:
        if len(block) < 2:
            continue

        # First line should be index
        try:
            index = int(block[0])
        except ValueError:
            continue

        # Second line should be timestamp
        ts_match = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', block[1])
        if not ts_match:
            continue

        start = parse_timestamp(ts_match.group(1))
        end = parse_timestamp(ts_match.group(2))

        # Rest is text
        text = ' '.join(block[2:])
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags

        result.append(SRTBlock(index=index, start_seconds=start, end_seconds=end, text=text))

    return result


def get_transcript_at_timestamp(blocks: list[SRTBlock], timestamp_seconds: float, window: int = 5) -> str:
    """Get transcript text around a specific timestamp."""
    relevant = []
    for block in blocks:
        # Include blocks within window seconds of timestamp
        if block.start_seconds <= timestamp_seconds + window and block.end_seconds >= timestamp_seconds - window:
            relevant.append(block.text)

    return ' '.join(relevant)


def find_visual_cues(blocks: list[SRTBlock]) -> list[dict]:
    """Find timestamps where visual content is likely being referenced."""
    cue_patterns = [
        (r'\byou can see\b', 'visual reference'),
        (r'\blook at\b', 'visual reference'),
        (r'\bcheck this out\b', 'demonstration'),
        (r'\blet me show\b', 'demonstration'),
        (r'\bhere we have\b', 'visual reference'),
        (r'\bthis is\b', 'introduction'),
        (r'\bon screen\b', 'visual reference'),
        (r'\bif you look\b', 'visual reference'),
        (r'\bwatch\b', 'demonstration'),
        (r'\bscreenshot\b', 'visual reference'),
        (r'\bopen up\b', 'action'),
        (r'\bgo to\b', 'navigation'),
        (r'\bclick\b', 'action'),
        (r'\bzoom in\b', 'visual reference'),
    ]

    cues = []
    for block in blocks:
        text_lower = block.text.lower()
        for pattern, cue_type in cue_patterns:
            if re.search(pattern, text_lower):
                cues.append({
                    'timestamp_seconds': int(block.start_seconds),
                    'type': cue_type,
                    'text': block.text[:100],
                })
                break  # One cue per block

    return cues


def find_topic_changes(blocks: list[SRTBlock], min_gap: float = 3.0) -> list[int]:
    """Find timestamps where there might be topic changes (gaps in speech)."""
    changes = []
    prev_end = 0

    for block in blocks:
        if block.start_seconds - prev_end > min_gap:
            changes.append(int(block.start_seconds))
        prev_end = block.end_seconds

    return changes


def get_key_timestamps(srt_content: str, max_frames: int = None) -> list[dict]:
    """Get key timestamps for frame extraction based on transcript analysis.

    Args:
        srt_content: SRT file content
        max_frames: Maximum frames to return (default from config)

    Returns:
        List of dicts with timestamp_seconds, type, and text
    """
    from config import MAX_FRAMES_FAST

    if max_frames is None:
        max_frames = MAX_FRAMES_FAST

    blocks = parse_srt(srt_content)

    if not blocks:
        return []

    # Find visual cues
    cues = find_visual_cues(blocks)

    # Find topic changes
    topic_changes = find_topic_changes(blocks)

    # Combine and deduplicate (within configurable window)
    all_timestamps = {}

    for cue in cues:
        ts = cue['timestamp_seconds']
        if ts not in all_timestamps:
            all_timestamps[ts] = cue

    for ts in topic_changes:
        if ts not in all_timestamps:
            all_timestamps[ts] = {'timestamp_seconds': ts, 'type': 'topic_change', 'text': ''}

    # Sort by timestamp
    sorted_ts = sorted(all_timestamps.values(), key=lambda x: x['timestamp_seconds'])

    # Deduplicate within window
    deduped = []
    last_ts = -KEY_TIMESTAMP_WINDOW * 2
    for item in sorted_ts:
        if item['timestamp_seconds'] - last_ts >= KEY_TIMESTAMP_WINDOW:
            deduped.append(item)
            last_ts = item['timestamp_seconds']

    # If too many, prioritize visual cues over topic changes
    if len(deduped) > max_frames:
        visual = [x for x in deduped if x['type'] != 'topic_change']
        other = [x for x in deduped if x['type'] == 'topic_change']
        deduped = visual[:max_frames]
        remaining = max_frames - len(deduped)
        if remaining > 0:
            deduped.extend(other[:remaining])
        deduped.sort(key=lambda x: x['timestamp_seconds'])

    return deduped


def _score_blocks_with_haiku(blocks: list[SRTBlock], intent: str) -> dict[int, dict]:
    """Score SRT blocks with Haiku. Returns {index: {visual, intent, reason}}.

    Chunked to keep each call small; caller handles fallback on empty result.
    """
    CHUNK = 100
    all_scores: dict[int, dict] = {}

    for i in range(0, len(blocks), CHUNK):
        chunk = blocks[i:i + CHUNK]
        lines = []
        for b in chunk:
            txt = b.text.replace("\n", " ").replace("\t", " ")[:200]
            lines.append(f"{b.index}\t[{int(b.start_seconds)}s]\t{txt}")
        block_dump = "\n".join(lines)

        prompt = f"""Rate transcript lines for frame-worthy moments.

USER INTENT:
{intent}

For each line, score:
- visual: 0.0-1.0 — does the speaker seem to reference something visible on screen?
  HIGH for "look at", "as you can see", "here's the diagram", pointing/demonstrating, showing UI or code.
  LOW for pure narration, storytelling, abstract talk, talking-head commentary.
- intent: 0.0-1.0 — is this line relevant to the user's intent above?
- reason: one short phrase (<12 words).

A moment is frame-worthy only when BOTH are high.

Return strict JSON (no prose, no markdown fences):
{{"scores": [{{"index": N, "visual": 0.0, "intent": 0.0, "reason": "..."}}, ...]}}

One entry per line, in order. Score all {len(chunk)} lines.

LINES:
{block_dump}
"""

        try:
            result = subprocess.run(
                [_CLAUDE_BIN, "--print", "--model", "haiku",
                 "--disallowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
                 "WebSearch", "WebFetch", "TodoWrite"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"  Scoring call failed: {e}")
            return {}

        if result.returncode != 0:
            print(f"  Scoring exited {result.returncode}: {result.stderr[:200]}")
            return {}

        m = re.search(r'\{[\s\S]*\}', result.stdout)
        if not m:
            continue
        try:
            data = json.loads(m.group())
        except json.JSONDecodeError:
            continue

        for s in data.get("scores", []):
            try:
                idx = int(s["index"])
                all_scores[idx] = {
                    "visual": float(s.get("visual", 0)),
                    "intent": float(s.get("intent", 0)),
                    "reason": str(s.get("reason", ""))[:140],
                }
            except (KeyError, ValueError, TypeError):
                continue

    return all_scores


def get_intent_aligned_timestamps(
    srt_content: str,
    intent: str,
    max_frames: int,
    debug_out: Optional[Path] = None,
) -> list[dict]:
    """Pick top-N timestamps where the transcript is both visually-referential
    and aligned with the user's intent.

    Falls back to get_key_timestamps() when intent is empty or scoring fails.

    If debug_out is given, writes the full scoring table there so the agent
    can show Lukas *why* frames were picked (or missed).
    """
    if not intent or not intent.strip():
        return get_key_timestamps(srt_content, max_frames=max_frames)

    blocks = parse_srt(srt_content)
    if not blocks:
        return []

    scores = _score_blocks_with_haiku(blocks, intent)
    if not scores:
        print("  Intent scoring returned nothing, falling back to regex cues")
        return get_key_timestamps(srt_content, max_frames=max_frames)

    scored: list[dict] = []
    for b in blocks:
        s = scores.get(b.index)
        if not s:
            continue
        combined = s["visual"] * s["intent"]
        scored.append({
            "timestamp_seconds": int(b.start_seconds),
            "type": "intent_aligned",
            "text": b.text[:200],
            "visual_score": round(s["visual"], 2),
            "intent_score": round(s["intent"], 2),
            "combined_score": round(combined, 3),
            "reason": s["reason"],
        })

    scored.sort(key=lambda x: x["combined_score"], reverse=True)

    picked: list[dict] = []
    picked_ts: list[int] = []
    for item in scored:
        if item["combined_score"] < 0.1:
            break
        ts = item["timestamp_seconds"]
        if any(abs(ts - pt) < KEY_TIMESTAMP_WINDOW for pt in picked_ts):
            continue
        picked.append(item)
        picked_ts.append(ts)
        if len(picked) >= max_frames:
            break

    picked.sort(key=lambda x: x["timestamp_seconds"])

    if debug_out:
        debug_out.write_text(json.dumps({
            "intent": intent,
            "picked_count": len(picked),
            "picked": picked,
            "all_scored_top": scored[:200],
        }, indent=2, ensure_ascii=False))

    return picked


def correlate_frames_with_transcript(frames_dir: Path, srt_content: str) -> list[dict]:
    """Create frame-transcript correlation for all frames in directory."""
    blocks = parse_srt(srt_content)

    if not blocks:
        return []

    correlations = []

    # Parse frame filenames for timestamps
    for frame_path in sorted(frames_dir.glob("frame_*.jpg")):
        # Extract timestamp from filename like frame_0078_09m40s.jpg
        match = re.search(r'_(\d+)m(\d+)s\.jpg$', frame_path.name)
        if match:
            minutes, seconds = int(match.group(1)), int(match.group(2))
            timestamp = minutes * 60 + seconds

            transcript_text = get_transcript_at_timestamp(blocks, timestamp, window=5)

            correlations.append({
                'frame': frame_path.name,
                'timestamp_seconds': timestamp,
                'timestamp_display': f"{minutes:02d}:{seconds:02d}",
                'transcript': transcript_text,
            })

    return correlations


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python transcript_utils.py <srt_file> [--cues|--correlate <frames_dir>]")
        sys.exit(1)

    srt_path = Path(sys.argv[1])
    srt_content = srt_path.read_text()

    if len(sys.argv) > 2 and sys.argv[2] == "--cues":
        cues = get_key_timestamps(srt_content)
        print(json.dumps(cues, indent=2))
    elif len(sys.argv) > 3 and sys.argv[2] == "--correlate":
        frames_dir = Path(sys.argv[3])
        correlations = correlate_frames_with_transcript(frames_dir, srt_content)
        print(json.dumps(correlations, indent=2))
    else:
        blocks = parse_srt(srt_content)
        print(f"Parsed {len(blocks)} blocks")
        print(f"Duration: {blocks[-1].end_seconds if blocks else 0:.0f} seconds")
