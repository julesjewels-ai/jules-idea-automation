"""Event Bus implementation for the Jules Automation Tool.

Provides a simple, synchronous in-memory event bus.
"""

from typing import Any
from src.core.interfaces import EventBus, EventHandler


class InMemoryEventBus(EventBus):
    """Simple in-memory event bus implementation."""

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._handlers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        """Subscribe a handler to the event bus.

        Args:
            handler: The handler to subscribe.
        """
        self._handlers.append(handler)

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers synchronously.

        Args:
            event: The event to publish.
        """
        for handler in self._handlers:
            handler.handle(event)
