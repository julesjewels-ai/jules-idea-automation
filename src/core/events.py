"""Event definitions and EventBus protocol for the application."""

from typing import Protocol, Type, Callable, Any, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime


class Event(BaseModel):
    """Base event model."""
    timestamp: datetime = Field(default_factory=datetime.now)


class WorkflowStarted(Event):
    """Event triggered when a workflow starts."""
    idea_title: str
    slug: str


class StepStarted(Event):
    """Event triggered when a specific workflow step starts."""
    step_name: str
    message: str


class StepCompleted(Event):
    """Event triggered when a specific workflow step completes successfully."""
    step_name: str
    message: str
    result: Any = None


class WorkflowCompleted(Event):
    """Event triggered when a workflow completes successfully."""
    # Ideally WorkflowResult, but keeping generic to avoid circular imports
    result: Any


class WorkflowFailed(Event):
    """Event triggered when a workflow fails."""
    error: str
    tip: str = ""


E = TypeVar("E", bound=Event)
Handler = Callable[[E], None]


class EventBus(Protocol):
    """Protocol for an event bus."""

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        ...

    def subscribe(self, event_type: Type[E], handler: Handler[E]) -> None:
        """Subscribe a handler to a specific event type."""
        ...
