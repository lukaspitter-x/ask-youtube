# CLAUDE.md

Guidance for Claude Code working in this repo. See `README.md` for the full user-facing docs.

## What this is

`ask-youtube` turns a YouTube URL into a magazine-grade analysis page answering one specific
question. Python (`yt-dlp` + `ffmpeg`) pulls the artefacts; in `deep` mode two Claude Code
sub-agents (`.claude/agents/frame-describer.md`, `video-analyzer.md`) describe frames and
synthesize the answer.

## Working here

- Run everything from the repo root — deep mode resolves agents via `./.claude/agents/`.
- Use the venv: `.venv/bin/python3 scripts/fetch.py ...`.
- Tests: `.venv/bin/python3 -m pytest tests/ -q`.
- `--intent` drives deep mode (frame scoring + THE ANSWER). Keep it specific.
- Never commit `.share_token` — it's auth, and `.gitignore`d.

## Self-improvement loop

This repo keeps two append-only logs so each session is smarter than the last:
`DECISIONS.md` (choices that shape the project) and `LESSONS.md` (debugging gotchas).

Every session:

1. **Read first.** Before acting on a task, read `DECISIONS.md` and `LESSONS.md`. Honor active
   decisions; don't re-litigate them or repeat a logged mistake.
2. **Append as you go.** When you make a decision that future-you would want to know, add it to
   `DECISIONS.md` (newest first, using the template). When a bug's cause surprised you, add a
   `LESSONS.md` entry. Log the moment it happens, not at the end.
3. **Commit at each important moment.** After a meaningful change or a new log entry, commit with
   a clear message. Don't batch a session's worth of work into one commit.

Keep all three files lean — short entries, no duplication. A log that's painful to read stops
getting read.
