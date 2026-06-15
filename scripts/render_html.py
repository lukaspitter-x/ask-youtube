#!/usr/bin/env python3
"""Render an `analysis.html` (and a `.share_token`) for a deep-mode output dir.

Inputs from the directory:
- `analysis.md` (required)        — markdown body produced by video-analyzer
- `metadata.json` (required)      — yt-dlp metadata; we use url, title, channel,
                                    duration, view_count
- `frames/*.jpg` (referenced)     — embedded images, served relative to the page

Optional:
- `<dir>/.answer` (text file)     — overrides the answer; falls back to first
                                    paragraph of the Summary section if missing.
                                    (When called from analyze_video.py, the
                                    `answer` kwarg is passed in directly.)

Outputs:
- `analysis.html`                 — self-contained except for YouTube IFrame API
                                    + Bunny Fonts CSS
- `.share_token`                  — 16-char URL-safe token, generated once and
                                    reused on re-render

CLI:
    python render_html.py <output-dir>

Programmatic:
    from render_html import render
    render(Path("media/youtube/260417-..."), answer="...")
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
from datetime import datetime, timezone
from html import escape as html_escape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import markdown


TEMPLATE_PATH = Path(__file__).parent / "templates" / "page.html"

# yt-dlp URL → 11-char video ID
_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/)([\w-]{11})")


def extract_video_id(url: str) -> str:
    if not url:
        return ""
    m = _VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)
    # Fallback: parse query
    try:
        q = parse_qs(urlparse(url).query)
        if "v" in q:
            return q["v"][0]
    except Exception:
        pass
    return ""


def format_duration(seconds: int | None) -> str:
    if not seconds:
        return ""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


def format_views(n: int | None) -> str:
    if not n:
        return ""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M views"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K views"
    return f"{n} views"


def derive_answer_from_markdown(md_text: str) -> str:
    """Pull the first non-trivial paragraph from the Summary section."""
    # Match "## Summary" through the next "##" or "---"
    m = re.search(r"##\s+Summary\s*\n+(.+?)(?=\n##\s|\n---|\Z)", md_text, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    block = m.group(1).strip()
    # First paragraph = up to first blank line
    para = block.split("\n\n", 1)[0].strip()
    # Strip inline markdown formatting
    para = re.sub(r"\*\*(.+?)\*\*", r"\1", para)
    para = re.sub(r"\*(.+?)\*", r"\1", para)
    para = re.sub(r"`([^`]+)`", r"\1", para)
    para = re.sub(r"\[(.+?)\]\([^)]+\)", r"\1", para)
    return para.strip()


def strip_top_h1(md_text: str) -> str:
    """The page already shows the title in the rail. Drop the H1 from the body."""
    return re.sub(r"\A#\s+[^\n]+\n+", "", md_text, count=1)


def get_or_create_share_token(out_dir: Path) -> str:
    token_file = out_dir / ".share_token"
    if token_file.exists():
        token = token_file.read_text().strip()
        if token:
            return token
    token = secrets.token_urlsafe(12)  # ~16 chars
    token_file.write_text(token + "\n")
    return token


def render(out_dir: Path, answer: str | None = None) -> Path:
    """Render analysis.html into out_dir. Returns the path to the written file."""
    out_dir = Path(out_dir).resolve()

    md_path = out_dir / "analysis.md"
    meta_path = out_dir / "metadata.json"
    if not md_path.exists():
        raise FileNotFoundError(f"analysis.md missing in {out_dir}")
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json missing in {out_dir}")

    md_text = md_path.read_text(encoding="utf-8")
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    # Resolve answer: explicit kwarg > .answer file > derived from Summary
    if not answer:
        answer_file = out_dir / ".answer"
        if answer_file.exists():
            answer = answer_file.read_text(encoding="utf-8").strip()
    if not answer:
        answer = derive_answer_from_markdown(md_text)
    if not answer:
        answer = "(No headline answer was generated for this run.)"

    # Drop the leading H1 (already in the rail)
    body_md = strip_top_h1(md_text)
    body_html = markdown.markdown(
        body_md,
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )

    title = metadata.get("title") or "Untitled"
    channel = metadata.get("channel") or ""
    video_id = extract_video_id(metadata.get("url", ""))
    duration = format_duration(metadata.get("duration"))
    views = format_views(metadata.get("view_count"))

    # Find the intent — it's in the markdown after "## Intent"
    intent_match = re.search(r"##\s+Intent\s*\n+(.+?)(?=\n##|\Z)", md_text, re.DOTALL | re.IGNORECASE)
    intent = intent_match.group(1).strip() if intent_match else ""
    intent = re.sub(r"\s+", " ", intent)

    # Build channel meta tagline
    upload = metadata.get("upload_date", "")
    if upload and len(upload) == 8:
        upload = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}"
    channel_meta_parts = [p for p in ["Video analysis", upload] if p]
    channel_meta = "  ·  ".join(channel_meta_parts).replace("·", '<span class="dot">·</span>')

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Token (created if first render)
    get_or_create_share_token(out_dir)

    page = (
        template
        .replace("__TITLE__", html_escape(title))
        .replace("__CHANNEL_META__", channel_meta)
        .replace("__VIDEO_TITLE__", html_escape(title))
        .replace("__CHANNEL__", html_escape(channel))
        .replace("__DURATION__", html_escape(duration))
        .replace("__VIEWS__", html_escape(views))
        .replace("__ANSWER__", html_escape(answer))
        .replace("__INTENT__", html_escape(intent or "(no intent recorded)"))
        .replace("__VIDEO_ID__", html_escape(video_id))
        .replace("__BODY__", body_html)
        .replace("__GENERATED_AT__", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    )

    html_path = out_dir / "analysis.html"
    html_path.write_text(page, encoding="utf-8")
    return html_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path, help="Path to a deep-mode output directory containing analysis.md")
    ap.add_argument("--answer", default=None, help="Override the headline answer (otherwise derived from Summary)")
    args = ap.parse_args()

    if not args.output_dir.exists():
        print(f"error: {args.output_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    html_path = render(args.output_dir, answer=args.answer)
    token = (args.output_dir / ".share_token").read_text().strip()
    print(f"Wrote {html_path}")
    print(f"Share token: {token}")
    # NB: opening the file directly (file://) breaks the embedded YouTube player
    # — the IFrame API rejects the null origin (Error 153). Serve over http instead.
    print("To view with a working player, serve it over http:")
    print(f"  python3 -m http.server 8000 --directory {html_path.parent}")
    print("  then open http://localhost:8000/analysis.html")


if __name__ == "__main__":
    main()
