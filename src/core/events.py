"""Domain events for the Jules Automation Tool.

These events represent significant lifecycle moments in the application.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class BaseDomainEvent(BaseModel):
    """Base class for all domain events."""
    event_type: str = Field(description="The type of the event.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the event occurred."
    )

    class Config:
        """Pydantic configuration."""
        frozen = True


class WorkflowStarted(BaseDomainEvent):
    """Event emitted when a workflow begins execution."""
    event_type: str = "workflow_started"
    idea_title: str
    idea_slug: str
    workflow_params: dict[str, Any]


class RepoCreated(BaseDomainEvent):
    """Event emitted when a GitHub repository is successfully created."""
    event_type: str = "repo_created"
    repo_url: str
    visibility: str  # public or private


class ScaffoldGenerated(BaseDomainEvent):
    """Event emitted when the project scaffold is generated and committed."""
    event_type: str = "scaffold_generated"
    file_count: int
    requirements: list[str]


class SessionCreated(BaseDomainEvent):
    """Event emitted when a Jules session is successfully initialized."""
    event_type: str = "session_created"
    session_id: str
    session_url: str
    source_id: str


class WorkflowCompleted(BaseDomainEvent):
    """Event emitted when the entire workflow completes successfully."""
    event_type: str = "workflow_completed"
    repo_url: str
    session_url: Optional[str] = None
    duration_seconds: float
