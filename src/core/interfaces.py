"""Core interfaces and protocols."""
from __future__ import annotations
from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class CacheProvider(Protocol):
    """Protocol for cache providers."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        ...

    def delete(self, key: str) -> None:
        """Remove a value from the cache."""
        ...
