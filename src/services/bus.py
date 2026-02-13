"""Concrete implementation of EventBus."""

import logging
from collections import defaultdict
from typing import Type, Any

from src.core.events import Event, Handler, E

logger = logging.getLogger(__name__)


class LocalEventBus:
    """A simple, synchronous, in-memory event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[Type[Event],
                                list[Handler[Any]]] = defaultdict(list)

    def subscribe(self, event_type: Type[E], handler: Handler[E]) -> None:
        """Subscribe a handler to a specific event type."""
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        event_type = type(event)

        # Notify handlers subscribed to this specific event type
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(
                        f"Error handling event {
                            event_type.__name__}: {e}")
