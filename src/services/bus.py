"""Event Bus implementation for the Jules Automation Tool."""

from __future__ import annotations

import logging
from typing import Any

from src.core.interfaces import EventBus, EventHandler

logger = logging.getLogger(__name__)


class LocalEventBus(EventBus):
    """Local, synchronous implementation of the EventBus protocol."""

    def __init__(self) -> None:
        """Initialize the local event bus."""
        self._subscribers: dict[type, list[EventHandler]] = {}

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: The handler to call when the event is published.

        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed handler {handler.__class__.__name__} to event {event_type.__name__}")

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The domain event to publish.

        """
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])

        logger.debug(f"Publishing event {event_type.__name__} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                handler.handle(event)
            except Exception as e:
                # We catch any exception thrown by a handler to prevent one bad handler
                # from crashing the entire workflow or other handlers.
                logger.error(f"Error handling event {event_type.__name__} in {handler.__class__.__name__}: {e}")
                # We don't raise here to allow other handlers to run.


class NullEventBus(EventBus):
    """Null Object implementation of the EventBus protocol.

    Used as a safe default when no event bus is provided, preventing
    the need for null checks throughout the codebase.
    """

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Do nothing when subscribing."""
        pass

    def publish(self, event: Any) -> None:
        """Do nothing when publishing."""
        pass
