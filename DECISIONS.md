# Decisions

Append-only log of decisions that shape this project. **Newest first.** Keep entries lean.

<!-- TEMPLATE — copy below this line, fill in, place at top of the log.
## YYYY-MM-DD — <short title>
- **Decision:** what we chose to do.
- **Context:** what prompted it / what was true at the time.
- **Rationale:** why this over the alternatives.
- **Tradeoff:** what we gave up or now have to live with.
- **Status:** Active | Superseded by <date> | Reverted
-->

---

## 2026-06-16 — Live heartbeat ticker for blocking deep-mode calls
- **Decision:** Added `scripts/progress.py` (`Heartbeat`) and wrapped the three long, silent `subprocess.run` calls — Haiku scoring (`transcript_utils.py`), the parallel frame-describer phase, and video-analyzer synthesis (`analyze_video.py`) — so each shows a ticking elapsed counter plus its timeout ceiling.
- **Context:** Deep mode goes silent for minutes inside captured subprocesses; a static "Synthesizing…" line is indistinguishable from a hang (the README even warned "don't kill it").
- **Rationale:** Certainty comes from something that visibly *moves*. A per-second repaint with a timeout ceiling tells the user it's alive and the worst-case wait. Cheap (one util + `with` wrappers), no pipeline restructuring.
- **Tradeoff:** Heartbeat writes to stderr on a background daemon thread; on non-TTY it degrades to a sparse 30s log line rather than a live counter. Per-chunk elapsed isn't tracked individually (only phase elapsed + done-count).
- **Status:** Active

## 2026-06-16 — Adopt a self-improving knowledge base
- **Decision:** Maintain `DECISIONS.md` and `LESSONS.md` as append-only logs, and have every session read both before acting.
- **Context:** Knowledge from past sessions was being lost; recurring mistakes and re-litigated choices.
- **Rationale:** A lean, durable log compounds across sessions without bloating CLAUDE.md.
- **Tradeoff:** Small per-session discipline cost (read + append + commit).
- **Status:** Active
