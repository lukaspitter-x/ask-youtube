#!/usr/bin/env python3
"""
Transcript Correction - Fast pattern-based fixing of auto-generated transcription errors.

Uses regex patterns to fix common transcription mistakes. Fast and reliable.
"""

from __future__ import annotations

import re
from pathlib import Path


# Common transcription error patterns
# Format: (pattern, replacement, flags)
# Add new patterns here as you encounter them
CORRECTION_PATTERNS = [
    # Tech terms
    (r'\bcloud code\b', 'Claude Code', re.IGNORECASE),
    (r'\bclaude code\b', 'Claude Code', re.IGNORECASE),
    (r'\bslashclaude\b', '/claude', re.IGNORECASE),
    (r'\breotion\b', 'Remotion', re.IGNORECASE),
    (r'\bchron job', 'cron job', re.IGNORECASE),
    (r'\bchron system\b', 'cron system', re.IGNORECASE),

    # Project names
    (r'\bmultbook\b', 'Maltbook', re.IGNORECASE),
    (r'\bmaltbook\b', 'Maltbook', re.IGNORECASE),
    (r'\bopenclaw\b', 'OpenClaw', re.IGNORECASE),
    (r'\bopen claw\b', 'OpenClaw', re.IGNORECASE),
    (r'\bcloudbot\b', 'ClaudBot', re.IGNORECASE),
    (r'\bclawbo\b', 'ClaudBot', re.IGNORECASE),
    (r'\bginnie\b', 'Genie', re.IGNORECASE),
    (r'\bproject genie\b', 'Project Genie', re.IGNORECASE),

    # Platform names
    (r' onx ', ' on X ', 0),
    (r'\bonx\b', 'on X', 0),

    # Clean up fillers (optional - can be commented out)
    # (r'\buh\b', '', 0),
    # (r'\bum\b', '', 0),
]


def correct_transcript_fast(srt_content: str) -> str:
    """Apply pattern-based corrections to transcript. Fast and reliable."""

    result = srt_content

    for pattern, replacement, *flags in CORRECTION_PATTERNS:
        flag = flags[0] if flags else 0
        result = re.sub(pattern, replacement, result, flags=flag)

    # Clean up multiple spaces
    result = re.sub(r'  +', ' ', result)

    return result


def srt_to_plain_text(srt_content: str) -> str:
    """Convert SRT to plain text, removing timestamps."""
    lines = []
    seen = set()

    for line in srt_content.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Skip subtitle numbers
        if re.match(r'^\d+$', line):
            continue
        # Skip timestamps
        if re.match(r'^\d{2}:\d{2}:\d{2}', line):
            continue
        # Skip HTML-like tags
        line = re.sub(r'<[^>]+>', '', line)

        if line and line not in seen:
            seen.add(line)
            lines.append(line)

    return ' '.join(lines)


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python correct_transcript.py <output_dir>")
        print("Example: python correct_transcript.py out/250130-ytb-my-video/")
        sys.exit(1)

    output_dir = Path(sys.argv[1])

    # Look for raw SRT first, then corrected, then any SRT
    srt_path = output_dir / "transcript_raw.srt"
    if not srt_path.exists():
        srt_path = output_dir / "transcript.srt"
    if not srt_path.exists():
        for f in output_dir.glob("transcript*.srt"):
            srt_path = f
            break

    if not srt_path.exists():
        print(f"Error: No SRT transcript found in {output_dir}")
        sys.exit(1)

    print(f"Loading {srt_path.name}...")
    srt_content = srt_path.read_text(encoding="utf-8")
    print(f"  {len(srt_content)} chars")

    print("Applying corrections...")
    corrected_srt = correct_transcript_fast(srt_content)

    # Save corrected SRT
    corrected_srt_path = output_dir / "transcript.srt"
    corrected_srt_path.write_text(corrected_srt, encoding="utf-8")
    print(f"  Saved: {corrected_srt_path}")

    # Show sample
    print("\nFirst 3 subtitle blocks:")
    blocks = corrected_srt.split('\n\n')[:3]
    for block in blocks:
        print(f"  {block.replace(chr(10), ' | ')}")


if __name__ == "__main__":
    main()
