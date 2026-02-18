"""Core interfaces and protocols for the application."""

from typing import Protocol, Optional, Any, runtime_checkable


@runtime_checkable
class CacheProvider(Protocol):
    """Interface for caching mechanisms."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The unique key for the cached item.

        Returns:
            The cached value if found, otherwise None.
        """
        ...

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value in the cache.

        Args:
            key: The unique key for the item.
            value: The value to store.
            ttl: Optional time-to-live in seconds.
        """
        ...

    def delete(self, key: str) -> None:
        """Remove a value from the cache.

        Args:
            key: The unique key to remove.
        """
        ...
