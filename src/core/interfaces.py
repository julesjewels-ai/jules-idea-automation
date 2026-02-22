"""Interfaces for the Jules Automation Tool."""

from typing import Protocol, Any, Optional


class CacheProvider(Protocol):
    """Protocol for a caching service."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value, or None if not found or expired.
        """
        ...

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds.
        """
        ...

    def delete(self, key: str) -> None:
        """Remove a value from the cache.

        Args:
            key: The cache key.
        """
        ...
