#!/usr/bin/env python3
"""
YouTube Video Fetcher - Downloads video content with tiered analysis modes.

Modes:
    fast     - Transcript + transcript-cued frames only (no agents, ~30 seconds)
    standard - Fast mode + frame-transcript correlation JSON
    deep     - Full frame analysis + synthesis with agents (slow, 10+ minutes)

Usage:
    python scripts/fetch.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python scripts/fetch.py "URL" --mode fast
    python scripts/fetch.py "URL" --mode standard --intent "Extract key demos"
    python scripts/fetch.py "URL" --mode deep --intent "Full analysis"
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import (
    BROWSER,
    MAX_FRAMES_FAST,
    MAX_FRAMES_DEEP_INTENT_AWARE,
    MAX_COMMENTS,
    COMMENTS_FETCH_LIMIT,
    FRAME_INTERVAL_FALLBACK,
    FRAME_START_OFFSET,
    OUTPUT_DIR,
    YTDLP_EXTRA_FLAGS,
    get_ytdlp_search_paths,
)
from extract_frames import extract_frames, extract_frames_at_timestamps
from correct_transcript import correct_transcript_fast
from transcript_utils import (
    parse_srt,
    get_key_timestamps,
    get_intent_aligned_timestamps,
    correlate_frames_with_transcript,
)


def check_dependencies():
    """Check if required dependencies are available."""
    if not shutil.which("ffmpeg"):
        print("Warning: ffmpeg not found. Audio extraction to mp3 may fail.")
        print("Install with: brew install ffmpeg")


def is_valid_youtube_url(url: str) -> bool:
    """Check if the URL is a valid YouTube URL."""
    patterns = [
        r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]+",
        r"^https?://youtu\.be/[\w-]+",
        r"^https?://(www\.)?youtube\.com/shorts/[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)


def sanitize_slug(title: str) -> str:
    """Convert title to a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def get_ytdlp_path() -> str:
    """Get the path to yt-dlp, preferring the SABR-enabled version."""
    # Check platform-specific paths from config
    for path in get_ytdlp_search_paths():
        if path.exists():
            return str(path)

    # Fall back to PATH
    if shutil.which("yt-dlp"):
        return "yt-dlp"

    raise RuntimeError("yt-dlp not found. Install with: pip install yt-dlp")


def run_ytdlp(args: list, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run yt-dlp with the given arguments + the configured extra flags."""
    cmd = [get_ytdlp_path()] + list(YTDLP_EXTRA_FLAGS) + args
    return subprocess.run(cmd, capture_output=capture_output, text=True)


def fetch_metadata(url: str) -> dict:
    """Fetch video metadata using yt-dlp."""
    print("Fetching metadata...")
    result = run_ytdlp(["--cookies-from-browser", BROWSER, "--dump-json", url])
    if result.returncode != 0:
        print(f"Error fetching metadata: {result.stderr}")
        sys.exit(1)

    data = json.loads(result.stdout)
    return {
        "title": data.get("title"),
        "description": data.get("description"),
        "upload_date": data.get("upload_date"),
        "channel": data.get("channel"),
        "channel_id": data.get("channel_id"),
        "duration": data.get("duration"),
        "view_count": data.get("view_count"),
        "like_count": data.get("like_count"),
        "url": url,
    }


def fetch_transcript(url: str, output_dir: Path) -> bool:
    """Fetch and save video transcript as SRT with timestamps."""
    print("Fetching transcript...")

    raw_srt_path = output_dir / "transcript_raw.srt"

    # Skip if already exists
    if raw_srt_path.exists():
        print("  Already exists, skipping...")
        return True

    # Try manual subtitles first
    result = run_ytdlp([
        "--cookies-from-browser", BROWSER,
        "--write-sub",
        "--sub-lang", "en",
        "--sub-format", "srt",
        "--skip-download",
        "-o", str(output_dir / "transcript"),
        url,
    ])

    srt_files = list(output_dir.glob("transcript*.srt"))
    vtt_files = list(output_dir.glob("transcript*.vtt"))

    # If no manual subs, try auto-generated
    if not srt_files and not vtt_files:
        print("  No manual captions, trying auto-generated...")
        result = run_ytdlp([
            "--cookies-from-browser", BROWSER,
            "--write-auto-sub",
            "--sub-lang", "en",
            "--sub-format", "srt",
            "--skip-download",
            "-o", str(output_dir / "transcript"),
            url,
        ])
        srt_files = list(output_dir.glob("transcript*.srt"))
        vtt_files = list(output_dir.glob("transcript*.vtt"))

    if not srt_files and not vtt_files:
        print("  No transcript available for this video.")
        return False

    # Keep the SRT file with timestamps
    sub_file = srt_files[0] if srt_files else vtt_files[0]
    shutil.move(str(sub_file), str(raw_srt_path))

    # Clean up any other subtitle files
    for f in output_dir.glob("transcript*.srt"):
        if f != raw_srt_path:
            f.unlink()
    for f in output_dir.glob("transcript*.vtt"):
        f.unlink()

    print(f"  Saved transcript_raw.srt")
    return True


def fetch_comments(url: str, output_dir: Path) -> bool:
    """Fetch top 20 comments."""
    print("Fetching comments...")

    comments_path = output_dir / "comments.json"
    if comments_path.exists():
        print("  Already exists, skipping...")
        return True

    result = run_ytdlp([
        "--cookies-from-browser", BROWSER,
        "--write-comments",
        "--extractor-args", f"youtube:max_comments={COMMENTS_FETCH_LIMIT},all,{COMMENTS_FETCH_LIMIT}",
        "--skip-download",
        "--dump-json",
        url,
    ])

    if result.returncode != 0:
        print("  Comments may be disabled for this video.")
        return False

    try:
        data = json.loads(result.stdout)
        comments_data = data.get("comments", [])

        if not comments_data:
            print("  No comments available.")
            return False

        sorted_comments = sorted(
            comments_data,
            key=lambda c: c.get("like_count", 0) or 0,
            reverse=True,
        )[:MAX_COMMENTS]

        comments = [
            {
                "author": c.get("author"),
                "text": c.get("text"),
                "likes": c.get("like_count", 0),
            }
            for c in sorted_comments
        ]

        comments_path.write_text(json.dumps(comments, indent=2, ensure_ascii=False))
        print(f"  Saved {len(comments)} comments")
        return True

    except (json.JSONDecodeError, KeyError) as e:
        print(f"  Error parsing comments: {e}")
        return False


def download_video(url: str, output_dir: Path) -> bool:
    """Download video in best quality mp4."""
    print("Downloading video...")

    video_path = output_dir / "video.mp4"
    if video_path.exists():
        print("  Already exists, skipping...")
        return True

    result = run_ytdlp([
        "--cookies-from-browser", BROWSER,
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", str(video_path),
        url,
    ], capture_output=False)

    if video_path.exists():
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"  Saved video ({size_mb:.1f} MB)")
        return True

    print("  Video download failed.")
    return False


def download_audio(url: str, output_dir: Path) -> bool:
    """Download audio as mp3."""
    print("Downloading audio...")

    audio_path = output_dir / "audio.mp3"
    if audio_path.exists():
        print("  Already exists, skipping...")
        return True

    result = run_ytdlp([
        "--cookies-from-browser", BROWSER,
        "-f", "ba/bestaudio",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", str(output_dir / "audio.%(ext)s"),
        url,
    ], capture_output=False)

    if audio_path.exists():
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        print(f"  Saved audio ({size_mb:.1f} MB)")
        return True

    print("  Audio download failed.")
    return False


def correct_transcript(output_dir: Path) -> bool:
    """Apply fast pattern-based transcript correction."""
    raw_srt_path = output_dir / "transcript_raw.srt"
    corrected_path = output_dir / "transcript.srt"

    if not raw_srt_path.exists():
        print("  No transcript to correct")
        return False

    if corrected_path.exists():
        print("  Already corrected, skipping...")
        return True

    print("Correcting transcript...")
    raw_content = raw_srt_path.read_text(encoding="utf-8")
    corrected = correct_transcript_fast(raw_content)
    corrected_path.write_text(corrected, encoding="utf-8")
    print("  Saved transcript.srt")
    return True


def extract_frames_smart(
    output_dir: Path,
    mode: str,
    max_frames: int | None = None,
    intent: str | None = None,
) -> list[Path]:
    """Extract frames based on mode.

    max_frames:
      None (default) — mode-driven behavior. fast/standard → transcript-cued
                       with MAX_FRAMES_FAST cap. deep+intent → intent-aligned
                       selector capped at MAX_FRAMES_DEEP_INTENT_AWARE. deep
                       without intent → scene detection (no cap).
      0              — skip frame extraction entirely.
      N > 0          — force transcript-cued extraction capped at N frames,
                       regardless of mode. In deep+intent mode, N overrides
                       the intent-aware cap but the selector is still used.

    intent:
      When set and mode=="deep", frames are picked via Haiku-scored
      (visual-reference × intent-alignment) on the transcript. A debug file
      `frames_selection.json` is written to output_dir.
    """
    video_path = output_dir / "video.mp4"
    frames_dir = output_dir / "frames"
    transcript_path = output_dir / "transcript.srt"

    if max_frames == 0:
        print("  max_frames=0, skipping frame extraction")
        return []

    if not video_path.exists():
        print("  No video file, skipping frames")
        return []

    # Check if frames already exist
    if frames_dir.exists() and list(frames_dir.glob("frame_*.jpg")):
        existing = list(frames_dir.glob("frame_*.jpg"))
        print(f"  Frames already exist ({len(existing)} frames), skipping...")
        return existing

    # Deep + intent: use the intent-aware selector. Cap defaults to the
    # tighter intent-aware constant unless --frames forces otherwise.
    if mode == "deep" and intent and intent.strip():
        cap = max_frames if (max_frames is not None and max_frames > 0) else MAX_FRAMES_DEEP_INTENT_AWARE
        print(f"Extracting frames (intent-aligned, cap={cap})...")

        if transcript_path.exists():
            srt_content = transcript_path.read_text()
            debug_out = output_dir / "frames_selection.json"
            key_moments = get_intent_aligned_timestamps(
                srt_content, intent, max_frames=cap, debug_out=debug_out,
            )
            if key_moments:
                timestamps = [m['timestamp_seconds'] for m in key_moments]
                print(f"  Selected {len(timestamps)} intent-aligned moments")
                frames = extract_frames_at_timestamps(video_path, frames_dir, timestamps)
                print(f"  Extracted {len(frames)} frames")
                return frames

        print("  Intent selector yielded nothing, falling back to scene detection...")
        frames = extract_frames(video_path, frames_dir)
        print(f"  Extracted {len(frames)} frames")
        return frames

    cue_mode = (mode in ("fast", "standard")) or (max_frames is not None and max_frames > 0)

    if cue_mode:
        cap = max_frames if (max_frames is not None and max_frames > 0) else MAX_FRAMES_FAST
        print(f"Extracting frames (transcript-cued, cap={cap})...")

        if transcript_path.exists():
            srt_content = transcript_path.read_text()
            key_moments = get_key_timestamps(srt_content, max_frames=cap)

            if key_moments:
                timestamps = [m['timestamp_seconds'] for m in key_moments]
                print(f"  Found {len(timestamps)} key moments in transcript")
                frames = extract_frames_at_timestamps(video_path, frames_dir, timestamps)
                print(f"  Extracted {len(frames)} frames")
                return frames

        # Fallback: interval-based extraction
        print("  No transcript cues, using interval extraction...")
        from extract_frames import get_video_duration
        duration = get_video_duration(video_path)
        timestamps = list(range(FRAME_START_OFFSET, int(duration), FRAME_INTERVAL_FALLBACK))
        if len(timestamps) > cap:
            step = len(timestamps) / cap
            timestamps = [timestamps[int(i * step)] for i in range(cap)]
        frames = extract_frames_at_timestamps(video_path, frames_dir, timestamps)
        print(f"  Extracted {len(frames)} frames")
        return frames

    # deep mode, no intent, no cap: full scene detection
    print("Extracting frames (scene detection)...")
    frames = extract_frames(video_path, frames_dir)
    print(f"  Extracted {len(frames)} frames")
    return frames


def create_frame_correlation(output_dir: Path) -> dict:
    """Create frame-transcript correlation JSON."""
    frames_dir = output_dir / "frames"
    transcript_path = output_dir / "transcript.srt"
    correlation_path = output_dir / "frame_correlation.json"

    if correlation_path.exists():
        print("  Correlation already exists, skipping...")
        return json.loads(correlation_path.read_text())

    if not frames_dir.exists() or not transcript_path.exists():
        return {}

    print("Creating frame-transcript correlation...")
    srt_content = transcript_path.read_text()
    correlations = correlate_frames_with_transcript(frames_dir, srt_content)

    correlation_path.write_text(json.dumps(correlations, indent=2, ensure_ascii=False))
    print(f"  Saved frame_correlation.json ({len(correlations)} frames)")
    return correlations


def run_deep_analysis(output_dir: Path, intent: str):
    """Run full agent-based analysis (slow)."""
    from analyze_video import analyze_video_with_agent

    print(f"\nRunning deep analysis...")
    print(f"Intent: {intent}\n")
    print("WARNING: This uses sub-agents and may take 10+ minutes.")

    analysis_md, frames_data = analyze_video_with_agent(output_dir, intent)
    print(f"  Saved analysis.md")


def print_summary(output_dir: Path):
    """Print summary of downloaded files."""
    print("\n" + "=" * 50)
    print("Download complete!")
    print(f"Output: {output_dir}")
    print("\nFiles:")
    for f in sorted(output_dir.iterdir()):
        if f.is_dir():
            file_count = len(list(f.iterdir()))
            print(f"  {f.name}/: {file_count} files")
        else:
            size = f.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} bytes"
            print(f"  {f.name}: {size_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube video with tiered analysis modes"
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--mode", "-m",
        choices=["fast", "standard", "deep"],
        default="standard",
        help="Analysis mode: fast (transcript+frames), standard (adds correlation), deep (full agents)"
    )
    parser.add_argument(
        "--intent", "-i",
        type=str,
        help="Analysis intent (required for deep mode)"
    )
    parser.add_argument(
        "--skip-video",
        action="store_true",
        help="Skip video/audio download (transcript and frames only)"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Cap extracted+analysed frames. 0 = none (transcript-only). N>0 = transcript-cued cap, overrides mode defaults. Default: mode-driven."
    )

    args = parser.parse_args()

    if not is_valid_youtube_url(args.url):
        print(f"Error: Invalid YouTube URL: {args.url}")
        sys.exit(1)

    if args.mode == "deep" and not args.intent:
        print("Error: --intent is required for deep mode")
        sys.exit(1)

    if args.mode == "deep" and args.frames == 0:
        print("Error: --frames 0 is incompatible with --mode deep (deep needs frames to analyse). Use --mode standard or raise --frames.")
        sys.exit(1)

    if args.frames is not None and args.frames < 0:
        print("Error: --frames must be >= 0")
        sys.exit(1)

    check_dependencies()

    # Fetch metadata first to get title for directory name
    metadata = fetch_metadata(args.url)

    date_str = datetime.now().strftime("%y%m%d")
    slug = sanitize_slug(metadata["title"])
    output_dir = OUTPUT_DIR / f"{date_str}-ytb-{slug}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput directory: {output_dir}")
    print(f"Mode: {args.mode}\n")

    # Save metadata
    metadata_path = output_dir / "metadata.json"
    if not metadata_path.exists():
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        print("Saved metadata.json")

    # Fetch transcript and comments
    fetch_transcript(args.url, output_dir)
    fetch_comments(args.url, output_dir)

    # Correct transcript
    correct_transcript(output_dir)

    # Download video/audio (unless skipped)
    if not args.skip_video:
        download_video(args.url, output_dir)
        download_audio(args.url, output_dir)

    # Extract frames (mode-dependent, optionally capped by --frames, intent-aware in deep)
    extract_frames_smart(output_dir, args.mode, max_frames=args.frames, intent=args.intent)

    # Create frame-transcript correlation (standard and deep modes, skipped if no frames)
    if args.mode in ["standard", "deep"] and args.frames != 0:
        create_frame_correlation(output_dir)

    # Run deep analysis if requested
    if args.mode == "deep" and args.intent:
        run_deep_analysis(output_dir, args.intent)

    print_summary(output_dir)


if __name__ == "__main__":
    main()
