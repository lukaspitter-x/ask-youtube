# AGENTS.md

> The single source of truth for **any** coding agent working in this repo —
> Claude Code, OpenAI Codex, OpenClaw / OpenCode, Hermes, Cursor, Goose, Aider,
> and anything else that reads `AGENTS.md`. Claude Code also reads `CLAUDE.md`,
> which is a thin layer that imports this file. **Edit this file, not the copies.**

## What this project is

`ask-youtube` turns a YouTube URL into a magazine-grade analysis page that answers
**one specific question** about the video. Plain Python (`yt-dlp` + `ffmpeg`) pulls
the artefacts (transcript, frames, comments, metadata); in `deep` mode two Claude
Code sub-agents describe the chosen frames and synthesize the answer into
`analysis.md` / `analysis.html`.

It is a **CLI tool**, not a library or a service. Entry points are scripts under
`scripts/`. There is no package install, no server, no database.

## Run it (copy-paste, from the repo root)

Always run from the repo root — `deep` mode resolves its sub-agents via
`./.claude/agents/`, so the working directory matters.

```bash
# One-time setup. MUST be Python 3.10+ (see Hardware & requirements below).
python3.12 -m venv .venv            # or any python >=3.10
.venv/bin/pip install -r requirements.txt

# Fast: transcript + key frames only (~30s, free, no Claude Code needed)
.venv/bin/python3 scripts/fetch.py "<youtube-url>" --mode fast --skip-video

# Standard (default): adds frame<->transcript correlation (~1 min, free)
.venv/bin/python3 scripts/fetch.py "<youtube-url>" --mode standard

# Deep: the full agent pipeline -> analysis.md + analysis.html
#   SLOW and COSTS MONEY. See timings below. Needs Claude Code signed in.
.venv/bin/python3 scripts/fetch.py "<youtube-url>" \
  --mode deep \
  --intent "<the specific question to answer>"

# Re-ask a new question on an already-downloaded video (skips the download)
.venv/bin/python3 scripts/analyze_video.py "output/<run-dir>/" \
  --intent "<a different question>"
```

`--intent` is the whole game in `deep` mode: it drives both frame scoring and the
headline answer. Be specific. `"summarize this"` is wasted money; `"what exact
CLAUDE.md patterns do they recommend, and why?"` is not.

**Viewing `analysis.html` — serve it over HTTP, don't open the file directly.**
The page embeds the YouTube player via the IFrame API, which rejects a `file://`
origin (you'll see *"Error 153 — Video player configuration error"*). The text,
frames, and timestamp links still work off disk, but the inline player needs an
http(s) origin:

```bash
python3 -m http.server 8000 --directory output/<run-dir>
# then open http://localhost:8000/analysis.html
```
(The template now degrades to a clickable thumbnail on `file://` instead of a dead
player, but HTTP is the way to actually play inline.)

## Test & verify

```bash
.venv/bin/python3 -m pytest tests/ -q          # unit tests (pure logic, no network/cost)
```

To smoke-test the real pipeline **for free**, run `--mode standard` on a short
video and confirm a `output/<date>-ytb-<slug>/` folder appears with
`transcript.srt` and `frames/`. Do **not** reach for `deep` mode just to verify
plumbing — it is slow and spends tokens.

## Hardware & requirements — read this before you run anything

Be honest with the user about this. Measured on an Apple-silicon Mac,
2026-06-16, on a 29.5-minute (1080p) video:

| Resource | Reality |
|---|---|
| **Python** | **3.10+ is a hard requirement.** The scripts use PEP 604 `X \| None` type syntax that is evaluated at runtime — **Python 3.9 crashes on import** (`TypeError: unsupported operand type(s) for \|`). `python3 --version` first; if it's <3.10, build the venv with `python3.12`/`python3.11`. |
| **ffmpeg** | Required for frame extraction + audio. `brew install ffmpeg` / `apt install ffmpeg`. Not bundled. |
| **Claude Code CLI** | Required for `deep` mode only. `claude` must be on PATH and signed in. `deep` mode shells out to it (a Haiku scoring pass + two sub-agents). `fast`/`standard` do **not** need it. |
| **GPU** | **None.** No CUDA, no local model weights. All "AI" work is offloaded to Claude's API via the CLI. A laptop is fine. |
| **CPU / RAM** | Modest. ffmpeg + Pillow + imagehash are light. The bottleneck is network + Claude API latency, not local compute. |
| **Disk** | **~290 MB per ~30-min 1080p video** (≈235 MB `video.mp4` + ≈42 MB `audio.mp3` + ≈23 MB of frames + JSON). Scales with length/resolution. Use `--skip-video` to drop the bulk; everything still works from the audio + frames. `output/` is `.gitignore`d. |
| **Network** | Downloads the **full video** (here: 196 MB) + audio unless `--skip-video`. Needs YouTube cookies from a signed-in browser — see Cookies. |
| **Time (honest)** | `fast` ≈ 30s · `standard` ≈ 1 min · **`deep` ≈ roughly the video's own length**. The 29.5-min video above took **~24 minutes** end-to-end, **not** the "~10 min" older docs imply. 10 min is a floor for short videos, not a typical figure. Tell the user a realistic range up front and **do not kill a deep run that looks idle** — it goes silent inside captured sub-processes (a heartbeat ticker exists but degrades to sparse logging when output isn't a TTY, e.g. backgrounded). |
| **Cost** | `fast`/`standard` are free. `deep` spends Claude tokens: ~$0.50–$2 per video depending on length and frame count. |

## Project layout

```
scripts/
  fetch.py            # main entry point: download + tiered analysis
  analyze_video.py    # re-run deep analysis on an existing output dir
  config.py           # all tunables, read from YTF_* env vars (see below)
  extract_frames.py   # ffmpeg scene-detect + perceptual de-dup
  correct_transcript.py, transcript_utils.py
  render_html.py      # analysis.md -> analysis.html
  progress.py         # Heartbeat ticker for long silent subprocess calls
  templates/page.html # HTML template for the rendered page
.claude/agents/       # deep-mode sub-agents (frame-describer, video-analyzer)
tests/                # pytest unit tests
output/               # generated runs (gitignored, can be hundreds of MB)
DECISIONS.md, LESSONS.md  # append-only project memory (see Conventions)
```

## Configuration (env vars, all optional)

Everything is tunable via `YTF_*` env vars with sensible defaults; see
`scripts/config.py` for the full list. Most-used:

| Var | Default | What |
|---|---|---|
| `YTF_OUTPUT_DIR` | `./output` | Where runs are written |
| `YTF_BROWSER` | `chrome` | Browser to pull YouTube cookies from |
| `YTF_MAX_FRAMES_DEEP_INTENT` | `40` | Cap on intent-scored frames in deep mode |
| `YTF_MAX_COMMENTS` | `20` | How many comments to keep |
| `ASK_YT_PUBLIC_URL` | *(unset)* | Base URL if serving pages behind a token gate |

## Cookies

YouTube now demands cookies to download most videos. By default the tool reads
them from Chrome. If your YouTube login is elsewhere:
`YTF_BROWSER=firefox .venv/bin/python3 scripts/fetch.py "<url>" --mode standard`.
A "No video formats found" / sign-in-wall error is almost always a cookie issue.

## Conventions for agents working here

- **Run from the repo root.** Deep mode resolves agents via `./.claude/agents/`.
- **Never commit `.share_token`** — it is auth, and is `.gitignore`d. Deep mode mints one.
- **Never commit `output/`** — it's `.gitignore`d and can be hundreds of MB.
- **Append-only memory:** before acting, read `DECISIONS.md` (choices that shape
  the project) and `LESSONS.md` (debugging gotchas); honor active decisions and
  don't repeat logged mistakes. When you make a shaping decision or hit a
  surprising bug, append an entry (newest first, lean). Commit only when the user asks.
- **Keep docs in sync:** this `AGENTS.md` is the source of truth. `README.md` is
  the user-facing version of the same facts; `CLAUDE.md` imports this file.
```
