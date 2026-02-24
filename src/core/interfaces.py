from typing import Protocol, Any, Optional

class CacheProvider(Protocol):
    """Protocol for caching providers."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        ...

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        ...
