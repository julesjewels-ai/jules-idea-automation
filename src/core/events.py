"""Core event system for the application.

This module defines the event bus, event listeners, and domain events used
throughout the application. It follows the Observer pattern to decouple
business logic from side effects like logging and reporting.
"""

from datetime import datetime
from typing import Protocol, Any, Optional
from pydantic import BaseModel, Field

from src.core.models import WorkflowResult


class Event(BaseModel):
    """Base event class."""

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Time the event occurred."
    )
    name: str = Field(description="Name of the event.")


class WorkflowStarted(Event):
    """Event triggered when a workflow starts."""

    name: str = "workflow_started"
    idea_title: str
    slug: str


class StepStarted(Event):
    """Event triggered when a workflow step starts."""

    name: str = "step_started"
    step_name: str


class StepCompleted(Event):
    """Event triggered when a workflow step completes successfully."""

    name: str = "step_completed"
    step_name: str
    result: Optional[Any] = None


class StepFailed(Event):
    """Event triggered when a workflow step fails."""

    name: str = "step_failed"
    step_name: str
    error: str


class WorkflowCompleted(Event):
    """Event triggered when a workflow completes successfully."""

    name: str = "workflow_completed"
    result: WorkflowResult


class WorkflowFailed(Event):
    """Event triggered when a workflow fails."""

    name: str = "workflow_failed"
    error: str


class EventListener(Protocol):
    """Protocol for event listeners."""

    def handle(self, event: Event) -> None:
        """Handle an incoming event.

        Args:
            event: The event to handle.
        """
        ...


class EventBus(Protocol):
    """Protocol for the event bus."""

    def subscribe(self, listener: EventListener) -> None:
        """Subscribe a listener to the bus.

        Args:
            listener: The listener to subscribe.
        """
        ...

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event to publish.
        """
        ...


class LocalEventBus:
    """Simple in-memory event bus implementation."""

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._listeners: list[EventListener] = []

    def subscribe(self, listener: EventListener) -> None:
        """Subscribe a listener to the bus."""
        self._listeners.append(listener)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        for listener in self._listeners:
            try:
                listener.handle(event)
            except Exception:
                # Suppress errors in listeners to prevent crashing the
                # main thread. In a production system, we would log this.
                pass
