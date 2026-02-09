"""Core interfaces and protocols for the application."""

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

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache.

        Args:
            key: The unique cache key.
            value: The value to store (must be JSON serializable).
        """
        ...
