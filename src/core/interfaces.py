"""Core interfaces and protocols for the Jules Automation Tool."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class ProjectRepository(Protocol[T]):
    """Protocol for project data persistence."""

    def save(self, item: T) -> None:
        """Save an item to the repository.

        Args:
        ----
            item: The domain model to save.

        """
        ...

    def get(self, item_id: str) -> T | None:
        """Retrieve an item by its unique identifier.

        Args:
        ----
            item_id: The unique identifier.

        Returns:
        -------
            The domain model if found, None otherwise.

        """
        ...

    def list_all(self) -> list[T]:
        """List all items in the repository.

        Returns
        -------
            A list of all domain models.

        """
        ...


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def handle(self, event: Any) -> None:
        """Handle an event.

        Args:
        ----
            event: The domain event to handle.

        """
        ...


class EventBus(Protocol):
    """Protocol for the application event bus."""

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
        ----
            event_type: The type of event to subscribe to.
            handler: The handler to call when the event is published.

        """
        ...

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers.

        Args:
        ----
            event: The domain event to publish.

        """
        ...


class CacheProvider(Protocol):
    """Protocol for caching mechanism."""

    def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve a value from the cache.

        Args:
        ----
            key: The unique cache key.

        Returns:
        -------
            The cached value as a dictionary, or None if not found.

        """
        ...

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a value in the cache.

        Args:
        ----
            key: The unique cache key.
            value: The value to cache (must be JSON-serializable).

        """
        ...
