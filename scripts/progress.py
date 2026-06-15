#!/usr/bin/env python3
"""
Progress signalling — a live "still working" heartbeat for blocking calls.

The deep-mode pipeline spends minutes inside blocking `subprocess.run` calls
(Haiku scoring, the frame-describer chunks, the video-analyzer synthesis). With
those calls captured, the terminal goes silent and an honest "it's working" is
indistinguishable from a hang. A *static* "Synthesizing…" line doesn't fix that
— the only convincing proof of life is something on screen that keeps moving.

`Heartbeat` repaints a single line with a ticking elapsed counter (and the
timeout ceiling, so the user knows the worst case) while a blocking call runs:

    with Heartbeat("Synthesizing analysis", timeout=300):
        subprocess.run(..., timeout=300)

On a non-TTY (logs/pipes, e.g. when driven from a bot under launchd) it can't
repaint, so it emits a sparse heartbeat line every 30s instead of flooding the
log. Use `.log()` to print a permanent line without clobbering the ticker, and
`.update()` to change the label mid-flight (e.g. a chunk counter).
"""

from __future__ import annotations

import sys
import threading
import time


def fmt_duration(seconds: float) -> str:
    """Render seconds as M:SS (e.g. 0:47, 3:05)."""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


class Heartbeat:
    """A live elapsed-time ticker around a blocking operation.

    Writes to stderr by default so it never pollutes captured stdout. Safe to
    use as a context manager; the background thread is a daemon and is always
    joined on exit.
    """

    _LOG_EVERY = 30.0  # non-TTY: emit a heartbeat line at most this often

    def __init__(self, label: str, timeout: float | None = None,
                 stream=None, interval: float = 1.0):
        self.label = label
        self.timeout = timeout
        self.stream = stream if stream is not None else sys.stderr
        self.interval = interval
        self.is_tty = bool(getattr(self.stream, "isatty", lambda: False)())
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._start = 0.0

    def __enter__(self) -> "Heartbeat":
        self._start = time.monotonic()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        elapsed = time.monotonic() - self._start
        with self._lock:
            if self.is_tty:
                self.stream.write("\r\033[K")  # clear the ticker line
            mark = "✓" if exc_type is None else "✗"
            self.stream.write(f"  {mark} {self.label} — {fmt_duration(elapsed)}\n")
            self.stream.flush()
        return False  # never suppress exceptions

    def update(self, label: str) -> None:
        """Change the ticker label mid-flight (e.g. 'chunk 3/4')."""
        with self._lock:
            self.label = label

    def log(self, message: str) -> None:
        """Print a permanent line above the ticker without garbling it."""
        with self._lock:
            if self.is_tty:
                self.stream.write("\r\033[K")
            self.stream.write(f"  {message}\n")
            self.stream.flush()

    def _ceiling(self) -> str:
        return f" (times out at {fmt_duration(self.timeout)})" if self.timeout else ""

    def _run(self) -> None:
        next_log = self._LOG_EVERY
        wait = self.interval if self.is_tty else 1.0
        while not self._stop.wait(wait):
            elapsed = time.monotonic() - self._start
            with self._lock:
                if self.is_tty:
                    self.stream.write(
                        f"\r  ⏳ {self.label}… {fmt_duration(elapsed)} elapsed{self._ceiling()}"
                    )
                    self.stream.flush()
                elif elapsed >= next_log:
                    self.stream.write(
                        f"  ⏳ {self.label}… still working, "
                        f"{fmt_duration(elapsed)} elapsed{self._ceiling()}\n"
                    )
                    self.stream.flush()
                    next_log += self._LOG_EVERY
