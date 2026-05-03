"""Simple rate limiting for polite fetching."""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Enforce a minimum delay between outbound requests.

    Thread-safe: uses a lock to protect the shared last-tick timestamp.
    """

    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self._last_tick = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """Sleep until the next request slot is available."""

        with self._lock:
            now = time.monotonic()
            remaining = self.delay_seconds - (now - self._last_tick)
            if remaining > 0:
                time.sleep(remaining)
            self._last_tick = time.monotonic()
