"""Polling utilities for waiting on external services."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def poll_until(
    condition: Callable[[], bool],
    timeout: int = 1800,
    interval: int = 10,
    on_poll: Callable[[int], None] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> bool:
    """Polls until a condition is met or timeout is reached.

    Args:
    ----
        condition: Callable that returns True when done
        timeout: Maximum seconds to wait
        interval: Seconds between polls
        on_poll: Optional callback with elapsed time
        sleep_fn: Sleep callable (default: time.sleep). Inject a no-op for fast tests.

    Returns:
    -------
        True if condition met, False if timeout

    """
    elapsed = 0
    while elapsed < timeout:
        if condition():
            return True
        if on_poll:
            on_poll(elapsed)
        sleep_fn(interval)
        elapsed += interval
    return False


def poll_with_result(
    check: Callable[[], tuple[bool, T]],
    timeout: int = 1800,
    interval: int = 30,
    on_poll: Callable[[int, str], None] | None = None,
    status_extractor: Callable[[], str] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[bool, T | None, int]:
    """Polls until completion, returning a result.

    Args:
    ----
        check: Callable that returns (is_complete, result)
        timeout: Maximum seconds to wait
        interval: Seconds between polls
        on_poll: Callback with (elapsed, status_message)
        status_extractor: Callable to get current status message
        sleep_fn: Sleep callable (default: time.sleep). Inject a no-op for fast tests.

    Returns:
    -------
        Tuple of (completed, result or None, elapsed_time)

    """
    elapsed = 0
    while elapsed < timeout:
        is_complete, result = check()
        if is_complete:
            return True, result, elapsed

        if on_poll:
            status = status_extractor() if status_extractor else "Working..."
            on_poll(elapsed, status)

        sleep_fn(interval)
        elapsed += interval

    return False, None, elapsed
