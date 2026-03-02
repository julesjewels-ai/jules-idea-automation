"""Core interfaces and protocols for the Jules Automation Tool."""

from typing import Protocol, Optional, Any, TypeVar


T = TypeVar('T')


class ProjectRepository(Protocol[T]):
    """Protocol for data persistence of domain models."""

    def save(self, item: T) -> None:
        """Save an item to the repository.

        Args:
            item: The domain model instance to save.
        """
        ...

    def get_all(self) -> list[T]:
        """Retrieve all items from the repository.

        Returns:
            A list of all saved domain model instances.
        """
        ...


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def handle(self, event: Any) -> None:
        """Handle an event.

        Args:
            event: The domain event to handle.
        """
        ...


class EventBus(Protocol):
    """Protocol for the application event bus."""

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: The handler to call when the event is published.
        """
        ...

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The domain event to publish.
        """
        ...


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
