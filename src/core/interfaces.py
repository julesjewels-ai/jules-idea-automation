"""Core interfaces and protocols for the Jules Automation Tool."""

from typing import Protocol, Optional, Any, TypeVar

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


class ProjectRepository(Protocol[T]):
    """Protocol for storing and retrieving domain models."""

    def save(self, result: T) -> None:
        """Save a model.

        Args:
            result: The model to save.
        """
        ...

    def get_by_slug(self, slug: str) -> Optional[T]:
        """Retrieve a model by its slug.

        Args:
            slug: The model slug.

        Returns:
            The model if found, else None.
        """
        ...

    def list_all(self) -> list[T]:
        """List all saved models.

        Returns:
            A list of all saved models.
        """
        ...
