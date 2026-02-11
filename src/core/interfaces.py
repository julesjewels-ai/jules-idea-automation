"""Core interfaces for the Jules Automation Tool."""

from typing import Protocol, Any, Optional


class CacheProvider(Protocol):
    """Protocol for caching mechanisms."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        ...
