#!/usr/bin/env python3
"""
Intelligent Frame Extraction - Extracts meaningful frames from videos.

Uses a hybrid approach:
1. FFmpeg scene detection to find candidate frames
2. Perceptual hash deduplication to remove similar frames
3. Minimum interval guarantee for coverage
"""

from __future__ import annotations

import shutil
import subprocess
import re
from pathlib import Path
from typing import Optional

from PIL import Image
import imagehash

from transcript_utils import format_timestamp_filename


def get_default_config() -> dict:
    """Default configuration for general content."""
    return {
        "scene_threshold": 0.3,
        "hash_threshold": 8,
        "min_interval_seconds": 10,
    }


CONTENT_CONFIGS = {
    "lecture": {"scene_threshold": 0.15, "hash_threshold": 5, "min_interval_seconds": 60},
    "tutorial": {"scene_threshold": 0.2, "hash_threshold": 6, "min_interval_seconds": 15},
    "documentary": {"scene_threshold": 0.3, "hash_threshold": 8, "min_interval_seconds": 10},
    "action": {"scene_threshold": 0.5, "hash_threshold": 12, "min_interval_seconds": 2},
}


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        return float(result.stdout.strip())
    return 0.0


def extract_scene_changes(video_path: Path, output_dir: Path, threshold: float) -> list[tuple[Path, float]]:
    """Use FFmpeg to extract frames at scene changes with timestamps."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use showinfo filter to get timestamps, output to stderr
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr",
        "-q:v", "2",
        str(output_dir / "scene_%04d.jpg"),
        "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse timestamps from showinfo output
    frames = sorted(output_dir.glob("scene_*.jpg"))
    timestamps = []
    for line in result.stderr.split('\n'):
        if 'pts_time:' in line:
            match = re.search(r'pts_time:\s*([\d.]+)', line)
            if match:
                timestamps.append(float(match.group(1)))

    # Pair frames with timestamps (fallback to 0 if parsing failed)
    frame_data = []
    for i, frame in enumerate(frames):
        ts = timestamps[i] if i < len(timestamps) else 0.0
        frame_data.append((frame, ts))

    return frame_data


def extract_frame_at_time(video_path: Path, output_path: Path, timestamp: float) -> tuple[Path, float]:
    """Extract a single frame at a specific timestamp."""
    cmd = [
        "ffmpeg", "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(output_path),
        "-y"
    ]
    subprocess.run(cmd, capture_output=True)
    return (output_path, timestamp)


def deduplicate_frames(frame_data: list[tuple[Path, float]], threshold: int = 8) -> list[tuple[Path, float]]:
    """Remove visually similar frames using perceptual hashing."""
    if not frame_data:
        return []

    unique = [frame_data[0]]
    last_hash = imagehash.phash(Image.open(frame_data[0][0]))

    for path, ts in frame_data[1:]:
        current_hash = imagehash.phash(Image.open(path))
        if current_hash - last_hash > threshold:
            unique.append((path, ts))
            last_hash = current_hash

    return unique


def ensure_minimum_coverage(
    video_path: Path,
    existing_frames: list[tuple[Path, float]],
    output_dir: Path,
    min_interval_seconds: float,
    duration: float
) -> list[tuple[Path, float]]:
    """Ensure at least one frame every min_interval_seconds."""
    if duration <= 0:
        return existing_frames

    final_frames = list(existing_frames)

    # Always ensure at least one frame at the start
    if not final_frames:
        coverage_dir = output_dir / "coverage"
        coverage_dir.mkdir(exist_ok=True)
        frame_path = coverage_dir / "interval_0000.jpg"
        frame_data = extract_frame_at_time(video_path, frame_path, 0.0)
        if frame_path.exists():
            final_frames.append(frame_data)

    # Calculate timestamps we need coverage for
    needed_timestamps = []
    t = min_interval_seconds
    while t < duration:
        needed_timestamps.append(t)
        t += min_interval_seconds

    # If we have very few frames, add interval frames
    expected_min_frames = max(1, int(duration / min_interval_seconds))
    if len(final_frames) < expected_min_frames:
        coverage_dir = output_dir / "coverage"
        coverage_dir.mkdir(exist_ok=True)

        for i, ts in enumerate(needed_timestamps):
            frame_path = coverage_dir / f"interval_{i+1:04d}.jpg"
            frame_data = extract_frame_at_time(video_path, frame_path, ts)
            if frame_path.exists():
                final_frames.append(frame_data)

    return final_frames


def cleanup_temp_frames(temp_dir: Path):
    """Remove temporary frame directory."""
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def move_to_final_location(frame_data: list[tuple[Path, float]], output_dir: Path) -> list[Path]:
    """Move all frames to final location with timestamp in filename."""
    # Sort by timestamp
    frame_data = sorted(frame_data, key=lambda x: x[1])

    final_frames = []
    for i, (frame, ts) in enumerate(frame_data, 1):
        ts_str = format_timestamp_filename(ts)
        final_path = output_dir / f"frame_{i:04d}_{ts_str}.jpg"
        shutil.move(str(frame), str(final_path))
        final_frames.append(final_path)
    return final_frames


def extract_frames_at_timestamps(
    video_path: Path,
    output_dir: Path,
    timestamps: list[int],
) -> list[Path]:
    """
    Extract frames at specific timestamps (fast, transcript-cued mode).

    Args:
        video_path: Path to the video file
        output_dir: Directory to save extracted frames
        timestamps: List of timestamps in seconds

    Returns:
        List of paths to extracted frames
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Deduplicate and sort timestamps
    timestamps = sorted(set(timestamps))

    frame_data = []
    for ts in timestamps:
        ts_str = format_timestamp_filename(ts)
        frame_path = output_dir / f"frame_cued_{ts_str}.jpg"
        extract_frame_at_time(video_path, frame_path, ts)
        if frame_path.exists():
            frame_data.append((frame_path, float(ts)))

    # Rename with sequential numbering
    final_frames = []
    for i, (frame, ts) in enumerate(frame_data, 1):
        ts_str = format_timestamp_filename(ts)
        final_path = output_dir / f"frame_{i:04d}_{ts_str}.jpg"
        if frame != final_path:
            shutil.move(str(frame), str(final_path))
        final_frames.append(final_path)

    return final_frames


def extract_frames(video_path: Path, output_dir: Path, config: dict = None) -> list[Path]:
    """
    Extract meaningful frames using hybrid approach:
    1. FFmpeg scene detection
    2. Perceptual hash deduplication
    3. Minimum interval guarantee

    Args:
        video_path: Path to the video file
        output_dir: Directory to save extracted frames
        config: Optional configuration dict with keys:
            - scene_threshold: FFmpeg scene change threshold (0.0-1.0)
            - hash_threshold: Perceptual hash difference threshold
            - min_interval_seconds: Minimum seconds between guaranteed frames

    Returns:
        List of paths to extracted frames
    """
    config = config or get_default_config()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get video duration
    duration = get_video_duration(video_path)

    # Step 1: Extract scene-change candidates
    candidates_dir = output_dir / "_candidates"
    candidates_dir.mkdir(exist_ok=True)

    candidate_frames = extract_scene_changes(
        video_path, candidates_dir, config["scene_threshold"]
    )

    # Step 2: Deduplicate using perceptual hashing
    unique_frames = deduplicate_frames(candidate_frames, config["hash_threshold"])

    # Step 3: Ensure minimum interval coverage
    all_frames = ensure_minimum_coverage(
        video_path, unique_frames, output_dir,
        config["min_interval_seconds"], duration
    )

    # Move to final location with clean naming
    final_frames = move_to_final_location(all_frames, output_dir)

    # Cleanup temporary directories
    cleanup_temp_frames(candidates_dir)
    coverage_dir = output_dir / "coverage"
    if coverage_dir.exists():
        cleanup_temp_frames(coverage_dir)

    return final_frames


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_frames.py <video_path> [output_dir] [content_type]")
        print(f"Content types: {', '.join(CONTENT_CONFIGS.keys())}")
        sys.exit(1)

    video = Path(sys.argv[1])
    if not video.exists():
        print(f"Error: Video not found: {video}")
        sys.exit(1)

    output = Path(sys.argv[2]) if len(sys.argv) > 2 else video.parent / "frames"

    content_type = sys.argv[3] if len(sys.argv) > 3 else None
    cfg = CONTENT_CONFIGS.get(content_type, get_default_config())

    print(f"Extracting frames from: {video}")
    print(f"Output directory: {output}")
    print(f"Config: {cfg}")

    frames = extract_frames(video, output, cfg)
    print(f"\nExtracted {len(frames)} unique frames")
