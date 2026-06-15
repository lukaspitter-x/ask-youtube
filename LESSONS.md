# Lessons

Append-only debugging lessons. **Newest first.** One lesson per gotcha. Keep entries lean.

<!-- TEMPLATE — copy below this line, fill in, place at top of the log.
## YYYY-MM-DD — <short title>  `tag1` `tag2`
- **Looked like:** the symptom as it first appeared.
- **Actually was:** the real root cause.
- **Fix:** what resolved it.
- **Don't:** the wrong turn to avoid next time.
- **More:** link / file:line / context (optional).
-->

---

## 2026-06-16 — Embedded YouTube player dead on `file://` (Error 153)  `html` `youtube`
- **Looked like:** opening `analysis.html` straight off disk showed
  "Error 153 — Video player configuration error" where the video should be; text
  and frames rendered fine.
- **Actually was:** the page uses the YouTube **IFrame Player API** (so timestamps
  can `seekTo()`), which validates the embedding **origin**. On `file://` the
  origin is `null`, so YouTube refuses to configure the player.
- **Fix:** serve over http (`python3 -m http.server --directory <run-dir>`), which
  gives a real origin. Template now also: passes `origin: location.origin`, adds an
  `onError` fallback, and on `file://` swaps the dead player for a clickable
  thumbnail instead of trying (and failing) to load the API.
- **Don't:** tell users to "just open it locally" — `file://` silently breaks the
  player. Documented in README + AGENTS.md.
- **Looked like:** `fetch.py --help` died instantly with
  `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` even
  though `pip install` and all imports succeeded.
- **Actually was:** the system `python3` was **3.9**, which evaluates PEP 604
  `X | None` annotations at runtime and can't handle them. The README says
  "Python 3.10+" but nothing enforces it, so the venv built happily on 3.9.
- **Fix:** rebuilt the venv with `python3.12 -m venv .venv`. Ran clean after.
- **Don't:** assume `python3` is ≥3.10. Check `python3 --version` before creating
  the venv; prefer an explicit `python3.12`/`python3.11`.
- **More:** documented in `AGENTS.md` (Hardware & requirements) and `README.md`.
