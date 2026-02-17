"""Domain events for the idea workflow."""

from __future__ import annotations

from src.core.interfaces import Event
from src.core.models import IdeaResponse, WorkflowResult


class WorkflowStarted(Event):
    """Event triggered when a workflow starts."""
    idea: IdeaResponse


class StepStarted(Event):
    """Event triggered when a workflow step starts."""
    step_name: str
    message: str


class StepCompleted(Event):
    """Event triggered when a workflow step completes successfully."""
    step_name: str
    result: str


class StepFailed(Event):
    """Event triggered when a workflow step fails."""
    step_name: str
    error: str


class StepProgress(Event):
    """Event triggered during a long-running step to update status."""
    step_name: str
    message: str


class RepoCreated(Event):
    """Event triggered when a GitHub repository is created."""
    repo_url: str


class ScaffoldGenerated(Event):
    """Event triggered when a project scaffold is generated."""
    file_count: int


class JulesSessionCreated(Event):
    """Event triggered when a Jules session is created."""
    session_id: str
    session_url: str


class WorkflowCompleted(Event):
    """Event triggered when a workflow completes successfully."""
    result: WorkflowResult


class WorkflowFailed(Event):
    """Event triggered when a workflow fails entirely."""
    error: str
