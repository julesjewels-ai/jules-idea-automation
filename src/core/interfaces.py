"""Core interfaces for the event system."""

from typing import Protocol, Any
from pydantic import BaseModel, ConfigDict


class Event(BaseModel):
    """Base model for all events."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    timestamp: float = 0.0  # Optional: could be set automatically, but keeping it simple for now


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def handle(self, event: Event) -> None:
        """Handle an event."""
        ...


class EventBus(Protocol):
    """Protocol for the event bus."""

    def subscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """Subscribe to an event type."""
        ...

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        ...
