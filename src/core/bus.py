"""Implementation of the Event Bus."""

from collections import defaultdict
from typing import Type
from src.core.interfaces import Event, EventBus, EventHandler


class LocalEventBus:
    """Synchronous in-memory event bus implementation."""

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: dict[Type[Event], list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        event_type = type(event)

        # Notify subscribers of this event type and all parent types
        for base_cls in event_type.__mro__:
            if issubclass(base_cls, Event) and base_cls in self._subscribers:
                for handler in self._subscribers[base_cls]:  # type: ignore
                    handler.handle(event)
