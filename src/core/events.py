"""Domain events for the workflow."""

from typing import Optional
from src.core.interfaces import Event
from src.core.models import IdeaResponse, WorkflowResult


class WorkflowStarted(Event):
    """Event emitted when the workflow starts."""
    idea: IdeaResponse


class StepStarted(Event):
    """Event emitted when a workflow step starts."""
    step_name: str
    description: str


class StepCompleted(Event):
    """Event emitted when a workflow step completes."""
    step_name: str
    result: Optional[str] = None


class RepoCreated(Event):
    """Event emitted when the GitHub repository is created."""
    username: str
    slug: str
    repo_url: str


class ScaffoldGenerated(Event):
    """Event emitted when the project scaffold is generated and committed."""
    files_count: int


class SessionWaitStarted(Event):
    """Event emitted when waiting for Jules indexing starts."""
    source_id: str
    timeout: int


class SessionCreated(Event):
    """Event emitted when the Jules session is created."""
    session_id: str
    session_url: str


class WorkflowCompleted(Event):
    """Event emitted when the workflow completes successfully."""
    result: WorkflowResult


class WorkflowFailed(Event):
    """Event emitted when the workflow fails."""
    error: str
    step_name: Optional[str] = None
