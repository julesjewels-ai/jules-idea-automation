"""Core interfaces and protocols."""

from typing import Protocol, Any, Optional


class CacheProvider(Protocol):
    """Protocol for cache providers."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The unique cache key.

        Returns:
            The cached value if found, None otherwise.
        """
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache.

        Args:
            key: The unique cache key.
            value: The value to cache (must be serializable).
            ttl: Optional time-to-live in seconds.
        """
        ...

    def delete(self, key: str) -> None:
        """Delete a value from the cache.

        Args:
            key: The unique cache key to delete.
        """
        ...
