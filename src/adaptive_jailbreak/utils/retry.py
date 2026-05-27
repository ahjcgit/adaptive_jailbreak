from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_call(func: Callable[[], T], max_attempts: int = 3, backoff_seconds: float = 1.0) -> T:
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as exc:  # pragma: no cover - exercised by callers
            last_error = exc
            if attempt < max_attempts - 1:
                time.sleep(backoff_seconds * (attempt + 1))
    assert last_error is not None
    raise last_error
