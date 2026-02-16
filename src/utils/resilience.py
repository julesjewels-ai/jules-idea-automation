"""Resilience utilities for handling transient failures."""

from __future__ import annotations

import time
import random
import logging
from typing import TypeVar, Callable, Any, Optional, Type
from src.core.interfaces import ResiliencePolicy
from src.utils.errors import AppError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResilienceError(AppError):
    """Base error for resilience failures."""
    pass


class MaxRetriesExceededError(ResilienceError):
    """Raised when operation fails after max retries."""
    pass


class RetryStrategy(ResiliencePolicy):
    """Implements exponential backoff with jitter retry strategy."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple[Type[Exception], ...] = (Exception,)
    ) -> None:
        """Initialize the retry strategy.

        Args:
            max_retries: Maximum number of retries (default: 3).
            base_delay: Initial delay in seconds (default: 1.0).
            max_delay: Maximum delay in seconds (default: 60.0).
            exponential_base: Base for exponential backoff (default: 2.0).
            jitter: Whether to add random jitter (default: True).
            retryable_exceptions: Tuple of exceptions to retry (default: Exception).
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def execute(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes the operation with retry logic."""
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Operation failed after {self.max_retries + 1} attempts: {e}"
                    )

        if last_exception:
            raise MaxRetriesExceededError(
                f"Max retries ({self.max_retries}) exceeded.",
                tip="Check the logs for details on the underlying error."
            ) from last_exception

        raise ResilienceError("Operation failed without exception.")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculates the delay for the next retry attempt."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        if self.jitter:
            delay *= (0.5 + random.random())
        return min(delay, self.max_delay)
