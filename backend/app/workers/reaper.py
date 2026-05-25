from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable

from app.orchestrator.scheduler import requeue_stuck_executions
from app.observability import metrics


class Reaper:
    def __init__(self, interval_seconds: int = 10, timeout_seconds: int = 60, logger: Callable | None = None):
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.logger = logger or (lambda *args, **kwargs: None)

    def _loop(self):
        self.logger("reaper: starting loop", self.interval_seconds)
        while not self._stop.is_set():
            try:
                count = requeue_stuck_executions(name=None, timeout_seconds=self.timeout_seconds)
                if count:
                    self.logger(f"reaper: requeued {count} tasks")
                    try:
                        if hasattr(metrics, "reaper_requeued_total"):
                            metrics.reaper_requeued_total.inc(count)  # type: ignore
                    except Exception:
                        pass
            except Exception as exc:
                self.logger("reaper error", exc)
            self._stop.wait(self.interval_seconds)
        self.logger("reaper: stopped")

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)


reaper = Reaper()
