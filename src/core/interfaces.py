"""Core interfaces and protocols for the Jules Automation Tool."""

from typing import Protocol, Optional, Any


class CacheProvider(Protocol):
    """Protocol for caching mechanism."""

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Retrieve a value from the cache.

        Args:
            key: The unique cache key.

        Returns:
            The cached value as a dictionary, or None if not found.
        """
        ...

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a value in the cache.

        Args:
            key: The unique cache key.
            value: The value to cache (must be JSON-serializable).
        """
        ...


class DomainEvent(Protocol):
    """Protocol for domain events."""
    pass


class EventHandler(Protocol):
    """Protocol for handling domain events."""

    def handle(self, event: Any) -> None:
        """Handle a domain event.

        Args:
            event: The domain event to handle.
        """
        ...


class EventBus(Protocol):
    """Protocol for event bus."""

    def subscribe(self, handler: EventHandler) -> None:
        """Subscribe a handler to the event bus.

        Args:
            handler: The handler to subscribe.
        """
        ...

    def publish(self, event: Any) -> None:
        """Publish an event to the event bus.

        Args:
            event: The event to publish.
        """
        ...
