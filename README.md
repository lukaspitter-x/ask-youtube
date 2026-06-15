# ask-youtube

> 🤖 **Optimised for [Claude](https://claude.com/claude-code).** This project is built and
> maintained with Claude Code, and ships a self-improving knowledge base (`CLAUDE.md`,
> `DECISIONS.md`, `LESSONS.md`) so every session gets sharper. **Any AI agent working in this
> repo must adopt those conventions:** read `CLAUDE.md` first, honor `DECISIONS.md` and
> `LESSONS.md`, append to them as you go, and commit at each milestone. See
> [Self-improvement loop](CLAUDE.md#self-improvement-loop).

**Stop watching YouTube. Start interrogating it.**

You paste a YouTube URL. A swarm of Claude Code agents watches the whole
thing for you — reads the transcript, *looks* at the frames, fact-checks
against the web — and hands you back a magazine-grade analysis page that
answers the one question you actually had.

No 47-minute "in this video we'll cover" preamble. No scrubbing the
timeline for the diagram at 12:30. Just the answer, with the receipts.

---

## 👀 First, look at what it makes

Because telling you is boring. This is the *actual output* — one HTML page
per video, generated end-to-end from a single command:

### "What's Anthropic's actual recommended Claude Code setup?"
![Anthropic Claude Code harness analysis](docs/examples/example-1-anthropic-harness.png)

### "What's the real opportunity in agentic engineering — and what do I do about it?"
![Agentic engineering analysis](docs/examples/example-2-agentic-engineering.png)

### "How did this guy build an AI agent that designs like him?"
![AI agent that designs like me analysis](docs/examples/example-3-designs-like-me.png)

Each page opens with **THE ANSWER** — the single most important sentence,
written to your exact question — then backs it with intent-scored key
frames, timestamped chapters, and supporting depth pulled from the web.

> 📄 Want to read full ones? The complete markdown for all three lives in
> [`examples/`](examples/). And here's a
> [full-length rendered page](docs/examples/example-1-anthropic-harness-full.png)
> so you can see how deep it goes.

---

## 🤔 What it actually does

Three speeds, depending on how much you care:

| Mode | Time | What you get | Cost |
|---|---|---|---|
| **`fast`** | ~30s | Transcript + key frames. Just the artefacts. | free |
| **`standard`** | ~1 min | Above + frame↔transcript correlation. | free |
| **`deep`** | **≈ the video's length** — a 30-min video took us **~24 min**, *not* 10 | The whole magic show: agents *describe every frame*, fact-check against the web, and synthesize the editorial HTML page you saw above. | ~$0.50–$2 in Claude tokens |

> ⏳ **Deep mode is genuinely slow — budget real time.** It scales with the
> video's length, not a flat number. On an Apple-silicon Mac a **29.5-minute
> video took ~24 minutes** end-to-end, and it goes *silent* for minutes at a
> time inside the agent sub-processes. **That's normal — don't kill it.**

Under the hood:

- **`yt-dlp`** grabs the video, audio, transcript, and top comments.
- **`ffmpeg`** pulls key frames (scene-detected, then perceptually de-duped).
- In **deep** mode, a cheap Haiku pass scores every transcript line on
  *(is it visual?) × (does it match what you asked?)* and picks the ~20–40
  frames worth looking at — so a vision model doesn't burn money describing
  the intro bumper.
- Two **Claude Code sub-agents** finish the job: one *describes* the chosen
  frames, one *synthesizes* everything into the final answer.

---

## 📦 What you need

This is a Claude Code-native tool. If you've got Claude Code, you're 90%
there.

- **Python 3.10+** — **hard requirement, not a suggestion.** The scripts use
  `X | None` type syntax that Python evaluates at runtime, so **3.9 crashes on
  import** (`TypeError: unsupported operand type(s) for |`). Check first with
  `python3 --version`; if it's older, build the venv with `python3.12` (or any
  3.10+).
- **[ffmpeg](https://ffmpeg.org/)** — `brew install ffmpeg` (macOS) /
  `apt install ffmpeg` (Linux). Not bundled.
- **[Claude Code](https://claude.com/claude-code)** — installed and signed in
  (`claude` on your PATH). Needed for **deep mode only**.
- A browser signed into YouTube (Chrome by default) — YouTube increasingly
  demands cookies to download. See [Cookies](#-cookies) below.

`fast` and `standard` modes don't need Claude Code at all — just Python + ffmpeg.

**Honest hardware notes:** **No GPU, no local model** — all the AI work is
offloaded to Claude's API, so a laptop is fine; CPU/RAM use is modest. The real
costs are **disk** (~**290 MB per ~30-min 1080p video**; use `--skip-video` to
drop most of it), **network** (it downloads the *full* video unless
`--skip-video`), and, for deep mode, **time + tokens** (see the ⏳ note above).

---

## 🚀 Install

```bash
git clone https://github.com/lukaspitter/ask-youtube.git
cd ask-youtube

python3 -m venv .venv          # python3 MUST be 3.10+ — else: python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

That's it. `yt-dlp` ships in `requirements.txt`, so you don't need a
system-wide install. (If `python3` is 3.9, the venv builds fine but the scripts
crash on import — rebuild with `python3.12 -m venv .venv`.)

---

## 🎬 Usage

**Three steps. No commands to memorise.**

1. Open this folder in [Claude Code](https://claude.com/claude-code)
   (`cd ask-youtube` then run `claude`).
2. Paste a **YouTube URL** and **the question you actually want answered**.
3. Wait. Claude does the rest and hands you back the analysis page.

That's the whole thing. For example, just type:

> **`https://youtu.be/VIDEO_ID — how does their auth flow actually work?`**

Claude figures out the rest, runs the pipeline for you, and tells you where your
`analysis.html` landed. (Deep analysis takes a while — see the ⏳ note up top.
That's normal, don't panic.)

### 💡 The one thing that matters: ask a *specific* question

The whole tool is built around your question — it's what decides which moments of
the video to look at and what the headline answer is written to. Vague in, vague
out:

- 🚫 "summarize this"
- ✅ "What are the exact CLAUDE.md patterns they recommend, and why?"

That's it. You can stop reading here. 👇 *Everything below is for people who want
to run it without Claude Code, or script it.*

<details>
<summary><b>Prefer the command line / want to script it?</b> (optional, advanced)</summary>

Run everything **from the repo root** — deep mode looks for its agents in
`./.claude/agents/`.

```bash
# Fast: just the transcript + frames, no AI, free
.venv/bin/python3 scripts/fetch.py "https://youtu.be/VIDEO_ID" --mode standard

# Deep: the full analysis answering your question
.venv/bin/python3 scripts/fetch.py "https://youtu.be/VIDEO_ID" \
  --mode deep \
  --intent "How does the auth flow actually work?"

# Re-ask a new question on a video you already pulled (skips the download)
.venv/bin/python3 scripts/analyze_video.py "output/260101-ytb-some-video/" \
  --intent "A totally different angle"
```

Handy flags: `--intent "..."` (your question, drives deep mode) · `--frames N`
(cap analysed frames; `0` = transcript only) · `--skip-video` (don't download the
video file) · `-m fast` (skip correlation, just dump artefacts).

</details>

---

## 🗂 What lands on disk

Each run drops a self-contained folder under `output/`:

```
output/YYMMDD-ytb-<slug>/
├── video.mp4               # the video (skip with --skip-video)
├── audio.mp3               # extracted audio
├── metadata.json           # title, channel, views, duration
├── transcript.srt          # cleaned transcript
├── comments.json           # top comments
├── frames/                 # extracted key frames
├── frames_selection.json   # deep+intent: why each frame was picked
├── analysis.md             # deep: the answer, in markdown
└── analysis.html           # deep: the shareable rendered page ⭐
```

`analysis.html` is a single, self-styled page (the editorial look you saw
up top).

> ▶️ **Serve it over HTTP to play the video.** The page embeds the YouTube
> player via the IFrame API, which rejects a `file://` origin — open it
> straight off disk and you'll see *"Error 153 — Video player configuration
> error"* where the video should be. Serve the folder instead:
> ```bash
> python3 -m http.server 8000 --directory output/YYMMDD-ytb-<slug>
> # then open http://localhost:8000/analysis.html
> ```
> The text, frames, and timestamp links work either way; only the inline
> player needs HTTP. Dropping it on any static host works for the same reason.

---

## ⚙️ Config

Everything's tunable via env vars — sensible defaults out of the box:

| Var | Default | What |
|---|---|---|
| `YTF_OUTPUT_DIR` | `./output` | Where runs get written |
| `YTF_BROWSER` | `chrome` | Browser to pull YouTube cookies from |
| `YTF_MAX_FRAMES_DEEP_INTENT` | `40` | Cap on intent-scored frames in deep mode |
| `YTF_MAX_COMMENTS` | `20` | How many comments to keep |
| `ASK_YT_PUBLIC_URL` | *(unset)* | Base URL if you serve pages behind a token gate |

---

## 🍪 Cookies

YouTube now wants cookies to download most videos. By default the tool reads
them from Chrome (`--cookies-from-browser chrome`). If your YouTube login
lives in another browser:

```bash
YTF_BROWSER=firefox .venv/bin/python3 scripts/fetch.py "URL" --mode standard
```

If downloads fail with "No video formats found" or a sign-in wall, this is
almost always the cause.

---

## 🧪 Tests

```bash
.venv/bin/python3 -m pytest tests/ -q
```

---

## A few honest notes

- **Deep mode is slow on purpose.** It's describing every chosen frame with
  a vision model and fact-checking against the web. ~10 minutes is normal.
  You won't have to guess whether it's stuck: every long step shows a live
  `⏳ … elapsed (times out at M:SS)` ticker, so a moving counter is your
  proof it's still working.
- **It costs a little money.** Deep runs spend Claude tokens — budget
  ~$0.50–$2 per video. `fast`/`standard` are free.
- **The frame-picker follows your intent.** If it missed a moment you cared
  about, sharpen `--intent` before reaching for `--frames`. Check
  `frames_selection.json` to see what it scored and why.
- **Share tokens are auth.** Deep mode mints a `.share_token`. Anyone with a
  URL containing it can read the page. It's `.gitignore`d for a reason —
  don't commit it.

---

## License

MIT — see [LICENSE](LICENSE). Built on [Claude Code](https://claude.com/claude-code),
[yt-dlp](https://github.com/yt-dlp/yt-dlp), and [ffmpeg](https://ffmpeg.org/).
