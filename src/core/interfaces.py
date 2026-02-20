"""Core interfaces and protocols for the application."""

from typing import Protocol, Optional, Any, runtime_checkable


@runtime_checkable
class CacheProvider(Protocol):
    """Protocol for cache providers."""

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Retrieve a value from the cache."""
        ...

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a value in the cache."""
        ...

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        ...
