"""Local event bus implementation."""

from __future__ import annotations

from typing import Type, Callable, Any
from collections import defaultdict
import logging

from src.core.interfaces import Event, EventBus

logger = logging.getLogger(__name__)


class LocalEventBus(EventBus):
    """Synchronous in-memory event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[
            Type[Event],
            list[Callable[[Any], None]]
        ] = defaultdict(list)

    def subscribe(
        self,
        event_type: Type[Event],
        handler: Callable[[Any], None]
    ) -> None:
        """Subscribe to an event type."""
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        event_type = type(event)

        # Notify subscribers for this specific event type
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error handling event {event_type.__name__}: {e}")
