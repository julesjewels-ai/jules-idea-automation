"""Event system for decoupling core logic from side effects."""

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Event(BaseModel):
    """Base event model."""

    name: str = Field(description="Name of the event")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event data"
    )


@runtime_checkable
class EventListener(Protocol):
    """Protocol for event listeners."""

    def on_event(self, event: Event) -> None:
        """Handle an event."""
        ...


@runtime_checkable
class EventBus(Protocol):
    """Protocol for the event bus."""

    def subscribe(self, listener: EventListener) -> None:
        """Subscribe a listener to all events."""
        ...

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        ...


class LocalEventBus:
    """Simple in-memory event bus implementation."""

    def __init__(self) -> None:
        self._listeners: list[EventListener] = []

    def subscribe(self, listener: EventListener) -> None:
        """Subscribe a listener to all events."""
        self._listeners.append(listener)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        for listener in self._listeners:
            try:
                listener.on_event(event)
            except Exception as e:
                # Prevent listener errors from crashing the app
                # For now, just print to stderr as a fallback
                import sys
                print(f"Error in event listener: {e}", file=sys.stderr)


# Domain Events

class WorkflowStarted(Event):
    """Event emitted when the workflow starts."""

    name: str = "workflow_started"


class StepStarted(Event):
    """Event emitted when a workflow step starts."""

    name: str = "step_started"


class StepCompleted(Event):
    """Event emitted when a workflow step completes."""

    name: str = "step_completed"


class RepoCreated(Event):
    """Event emitted when a GitHub repository is created."""

    name: str = "repo_created"


class ScaffoldGenerated(Event):
    """Event emitted when a project scaffold is generated."""

    name: str = "scaffold_generated"


class SessionCreated(Event):
    """Event emitted when a Jules session is created."""

    name: str = "session_created"


class WorkflowCompleted(Event):
    """Event emitted when the workflow completes successfully."""

    name: str = "workflow_completed"


class WorkflowFailed(Event):
    """Event emitted when the workflow fails."""

    name: str = "workflow_failed"
