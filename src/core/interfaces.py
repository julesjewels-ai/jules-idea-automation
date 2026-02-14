"""Interfaces for the Jules Automation Tool."""

from typing import Any, Optional, Protocol


class CacheProvider(Protocol):
    """Protocol for cache providers."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The unique key for the cached item.

        Returns:
            The cached value if found, None otherwise.
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache.

        Args:
            key: The unique key for the item.
            value: The value to store (must be serializable).
        """
        ...

    def delete(self, key: str) -> None:
        """Remove a value from the cache.

        Args:
            key: The unique key for the item to remove.
        """
        ...

    def clear(self) -> None:
        """Clear all cached values."""
        ...
