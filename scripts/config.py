#!/usr/bin/env python3
"""
Configuration for youtube-fetcher.

Centralizes all configurable values that were previously hardcoded.
"""

import os
import platform
from pathlib import Path

# Browser for cookies (can be overridden via env var)
BROWSER = os.environ.get("YTF_BROWSER", "chrome")

# Extra yt-dlp flags applied to every call. The ejs:github remote components
# fetch the JS challenge solver YouTube now requires for most format URLs.
# Without this flag yt-dlp errors with "No video formats found" on most videos.
YTDLP_EXTRA_FLAGS = os.environ.get(
    "YTF_YTDLP_FLAGS", "--remote-components ejs:github"
).split()

# Frame extraction limits
MAX_FRAMES_FAST = int(os.environ.get("YTF_MAX_FRAMES_FAST", "30"))
MAX_FRAMES_DEEP = int(os.environ.get("YTF_MAX_FRAMES_DEEP", "100"))
# Cap for deep mode when intent-aware selection is active. Kept lower than
# MAX_FRAMES_DEEP because we're picking on-topic frames, not dumping scenes —
# 30-40 well-scored frames beat 100 noisy ones for synthesis quality.
MAX_FRAMES_DEEP_INTENT_AWARE = int(os.environ.get("YTF_MAX_FRAMES_DEEP_INTENT", "40"))

# Comment fetching
MAX_COMMENTS = int(os.environ.get("YTF_MAX_COMMENTS", "20"))
COMMENTS_FETCH_LIMIT = int(os.environ.get("YTF_COMMENTS_FETCH_LIMIT", "100"))

# Frame extraction intervals (seconds)
FRAME_INTERVAL_FALLBACK = int(os.environ.get("YTF_FRAME_INTERVAL", "30"))
FRAME_START_OFFSET = int(os.environ.get("YTF_FRAME_START_OFFSET", "10"))

# Transcript correction patterns file (optional external override)
CORRECTION_PATTERNS_FILE = os.environ.get("YTF_PATTERNS_FILE", None)

# Deduplication window for key timestamps (seconds)
KEY_TIMESTAMP_WINDOW = int(os.environ.get("YTF_KEY_TIMESTAMP_WINDOW", "5"))

# Output directory — defaults to <repo>/output/. Override with YTF_OUTPUT_DIR.
# This file lives at .../scripts/config.py, so repo root is .parent x 2.
_REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.environ.get("YTF_OUTPUT_DIR") or (_REPO_ROOT / "output"))


def get_ytdlp_search_paths() -> list[Path]:
    """Get platform-specific paths to search for yt-dlp.

    Prefer the project's own .venv (kept in lockstep with requirements.txt),
    then Homebrew (kept current via `brew upgrade`), then user-site Python
    installs (which can rot — older versions break on YouTube changes)."""
    system = platform.system()
    paths = []

    # Project venv first — installed via requirements.txt
    paths.append(_REPO_ROOT / ".venv" / "bin" / "yt-dlp")

    if system == "Darwin":  # macOS
        # Homebrew direct (auto-updated)
        paths.append(Path("/opt/homebrew/bin/yt-dlp"))
        paths.append(Path("/usr/local/bin/yt-dlp"))
        # User Python installs (can be stale)
        for version in ["3.13", "3.12", "3.11", "3.10", "3.9"]:
            paths.append(Path.home() / f"Library/Python/{version}/bin/yt-dlp")

    elif system == "Linux":
        # Common Linux locations
        paths.append(Path.home() / ".local/bin/yt-dlp")
        paths.append(Path("/usr/local/bin/yt-dlp"))
        paths.append(Path("/usr/bin/yt-dlp"))
        # pipx
        paths.append(Path.home() / ".local/pipx/venvs/yt-dlp/bin/yt-dlp")

    elif system == "Windows":
        # Common Windows locations
        paths.append(Path.home() / "AppData/Local/Programs/yt-dlp/yt-dlp.exe")
        paths.append(Path.home() / "scoop/shims/yt-dlp.exe")

    return paths
