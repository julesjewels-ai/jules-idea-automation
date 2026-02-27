"""Domain events for the Jules Automation Tool."""

from __future__ import annotations

import time
from typing import Optional
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(description="Unique identifier for the event.")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of when the event occurred.")


class WorkflowStarted(DomainEvent):
    """Event emitted when an idea workflow starts."""

    idea_title: str
    idea_slug: str
    category: Optional[str] = None


class WorkflowCompleted(DomainEvent):
    """Event emitted when an idea workflow successfully completes."""

    idea_title: str
    idea_slug: str
    repo_url: str
    session_id: Optional[str] = None
    session_url: Optional[str] = None
