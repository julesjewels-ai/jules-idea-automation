"""Core interfaces and protocols."""

from __future__ import annotations

from typing import Any, Optional, Protocol


class CacheProvider(Protocol):
    """Interface for cache providers."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The unique cache key.

        Returns:
            The cached value or None if not found.
        """
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the cache.

        Args:
            key: The unique cache key.
            value: The value to store.
            ttl: Optional time-to-live in seconds.
        """
        ...
