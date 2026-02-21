"""Tests for the console reporter."""

from unittest.mock import Mock, call
from src.core.interfaces import Event, EventBus
from src.core.events import WorkflowStarted, RepoCreated, WorkflowFailed
from src.core.models import IdeaResponse
from src.services.reporting import ConsoleReporter


def test_reporter_subscribes_to_events():
    """Test that the reporter subscribes to all relevant events."""
    bus = Mock(spec=EventBus)
    reporter = ConsoleReporter(bus)

    # Check that subscribe was called multiple times
    assert bus.subscribe.called
    assert bus.subscribe.call_count >= 5  # At least the main events


def test_reporter_handles_workflow_started(capsys):
    """Test handling of WorkflowStarted event."""
    bus = Mock(spec=EventBus)
    reporter = ConsoleReporter(bus)

    idea = IdeaResponse(
        title="Test Idea",
        description="A test idea",
        slug="test-idea",
        tech_stack=[],
        features=[]
    )
    event = WorkflowStarted(idea=idea)

    reporter.handle(event)

    captured = capsys.readouterr()
    assert "Test Idea" in captured.out
    assert "test-idea" in captured.out
    assert "STARTING WORKFLOW" in captured.out


def test_reporter_handles_repo_created(capsys):
    """Test handling of RepoCreated event."""
    bus = Mock(spec=EventBus)
    reporter = ConsoleReporter(bus)

    event = RepoCreated(
        username="user",
        slug="test-repo",
        repo_url="https://github.com/user/test-repo"
    )

    reporter.handle(event)

    captured = capsys.readouterr()
    assert "https://github.com/user/test-repo" in captured.out
    assert "GitHub repository created" in captured.out


def test_reporter_handles_workflow_failed(capsys):
    """Test handling of WorkflowFailed event."""
    bus = Mock(spec=EventBus)
    reporter = ConsoleReporter(bus)

    event = WorkflowFailed(
        error="Something went wrong",
        step_name="create_repo"
    )

    reporter.handle(event)

    captured = capsys.readouterr()
    assert "WORKFLOW FAILED" in captured.out
    assert "Something went wrong" in captured.out
    assert "create_repo" in captured.out
