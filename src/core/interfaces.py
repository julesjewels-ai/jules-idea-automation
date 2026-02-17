"""Core interfaces and protocols."""

from __future__ import annotations

from typing import Protocol, Type, Callable, Any
from pydantic import BaseModel


class Event(BaseModel):
    """Base class for all domain events."""
    pass


class EventBus(Protocol):
    """Interface for an event bus."""

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        ...

    def subscribe(self, event_type: Type[Event], handler: Callable[[Any], None]) -> None:
        """Subscribe to an event type.

        Note: handler takes Any to allow specific Event subclasses without type checker complaints,
        though at runtime it will be the specific event type.
        """
        ...
