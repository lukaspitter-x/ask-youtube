# CLAUDE.md

Guidance for **Claude Code** in this repo. Everything project-wide — what this is,
how to run it, test commands, **hardware & requirements, costs, timings, cookies,
config, layout** — lives in **[AGENTS.md](AGENTS.md)**, the shared source of truth
for every agent. Read it first.

@AGENTS.md

The rest of this file is only the Claude Code-specific layer.

## Claude-specific notes

- **Deep-mode sub-agents** live in `./.claude/agents/` (`frame-describer.md`,
  `video-analyzer.md`). Deep mode resolves them by path, so always run from the
  repo root.
- `fast`/`standard` modes don't invoke Claude at all — they're pure Python.
- Deep mode shells out to `claude --print --model haiku` for frame scoring, then
  the two sub-agents. It is slow (~the video's length) and spends tokens — see the
  Hardware & requirements table in AGENTS.md before kicking one off, and warn the
  user about time/cost up front.

## Self-improvement loop

This repo keeps two append-only logs so each session is smarter than the last:
`DECISIONS.md` (choices that shape the project) and `LESSONS.md` (debugging gotchas).

Every session:

1. **Read first.** Before acting on a task, read `DECISIONS.md` and `LESSONS.md`.
   Honor active decisions; don't re-litigate them or repeat a logged mistake.
2. **Append as you go.** When you make a decision future-you would want to know,
   add it to `DECISIONS.md` (newest first, using the template). When a bug's cause
   surprised you, add a `LESSONS.md` entry. Log the moment it happens.
3. **Commit when the user asks.** After a meaningful change or a new log entry,
   offer to commit with a clear message; don't batch a session's work into one.

Keep all three files lean — short entries, no duplication. A log that's painful to
read stops getting read.
