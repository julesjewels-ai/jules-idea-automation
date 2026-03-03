"""Core interfaces and protocols for the Jules Automation Tool."""

from typing import Protocol, Optional, Any, TypeVar, Generic

T = TypeVar('T')


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


class ProjectRepository(Protocol, Generic[T]):
    """Protocol for project repositories."""

    def save(self, item: T) -> None:
        """Save an item to the repository.

        Args:
            item: The item to save.
        """
        ...

    def get(self, key: str) -> Optional[T]:
        """Retrieve an item from the repository.

        Args:
            key: The unique key for the item.

        Returns:
            The retrieved item, or None if not found.
        """
        ...

    def list_all(self) -> list[T]:
        """List all items in the repository.

        Returns:
            A list of all items.
        """
        ...
