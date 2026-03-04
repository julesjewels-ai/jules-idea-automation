"""Domain events for the Jules Automation Tool."""

from __future__ import annotations

import time

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(description="Unique identifier for the event.")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of when the event occurred.")


class WorkflowStarted(DomainEvent):
    """Event emitted when an idea workflow starts."""

    idea_title: str
    idea_slug: str
    category: str | None = None


class WorkflowCompleted(DomainEvent):
    """Event emitted when an idea workflow successfully completes."""

    idea_title: str
    idea_slug: str
    repo_url: str
    session_id: str | None = None
    session_url: str | None = None
