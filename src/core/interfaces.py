"""Core interfaces and protocols for the application."""

from typing import Any, Optional, Protocol


class CacheProvider(Protocol):
    """Protocol for a cache provider."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The unique key for the cached item.

        Returns:
            The cached value if found, None otherwise.
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: The unique key for the cached item.
            value: The value to cache.
        """
        ...

    def delete(self, key: str) -> None:
        """Delete a value from the cache.

        Args:
            key: The unique key for the cached item.
        """
        ...
