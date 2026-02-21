"""Tests for the workflow with event system."""

import pytest
from unittest.mock import Mock, call
from src.core.workflow import IdeaWorkflow
from src.services.github import GitHubClient
from src.services.gemini import GeminiClient
from src.services.jules import JulesClient
from src.core.interfaces import EventBus
from src.core.events import (
    WorkflowStarted, RepoCreated, ScaffoldGenerated,
    SessionWaitStarted, SessionCreated, WorkflowCompleted, WorkflowFailed
)


@pytest.fixture
def mock_github():
    mock = Mock(spec=GitHubClient)
    mock.get_user.return_value = {"login": "testuser"}
    mock.create_files.return_value = {"files_created": 5}
    return mock


@pytest.fixture
def mock_gemini():
    mock = Mock(spec=GeminiClient)
    mock.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    return mock


@pytest.fixture
def mock_jules():
    mock = Mock(spec=JulesClient)
    mock.source_exists.return_value = True
    mock.create_session.return_value = {"id": "session-123", "url": "http://jules/s/123"}
    return mock


@pytest.fixture
def mock_bus():
    return Mock(spec=EventBus)


def test_workflow_execute_emits_events(mock_github, mock_gemini, mock_jules, mock_bus):
    """Test that the workflow emits expected events during execution."""
    workflow = IdeaWorkflow(
        github=mock_github,
        gemini=mock_gemini,
        jules=mock_jules,
        bus=mock_bus
    )

    idea_data = {
        "title": "Test App",
        "description": "A test application",
        "slug": "test-app",
        "tech_stack": ["Python"],
        "features": ["Feature 1"]
    }

    result = workflow.execute(idea_data, private=True, timeout=10)

    # Check that events were published
    assert mock_bus.publish.call_count >= 5  # At least start, repo, scaffold, wait, session, complete

    # Verify specific events (checking types for simplicity here,
    # could verify attributes too)
    calls = mock_bus.publish.call_args_list

    # First event should be WorkflowStarted
    assert isinstance(calls[0][0][0], WorkflowStarted)
    assert calls[0][0][0].idea.title == "Test App"

    # Should have RepoCreated
    assert any(isinstance(call[0][0], RepoCreated) for call in calls)

    # Should have ScaffoldGenerated
    assert any(isinstance(call[0][0], ScaffoldGenerated) for call in calls)

    # Should have SessionWaitStarted
    assert any(isinstance(call[0][0], SessionWaitStarted) for call in calls)

    # Should have SessionCreated
    assert any(isinstance(call[0][0], SessionCreated) for call in calls)

    # Last event should be WorkflowCompleted
    assert isinstance(calls[-1][0][0], WorkflowCompleted)
    assert calls[-1][0][0].result == result


def test_workflow_failed_event(mock_github, mock_gemini, mock_jules, mock_bus):
    """Test that WorkflowFailed is emitted on error."""
    mock_github.create_repo.side_effect = Exception("GitHub API Error")

    workflow = IdeaWorkflow(
        github=mock_github,
        gemini=mock_gemini,
        jules=mock_jules,
        bus=mock_bus
    )

    idea_data = {
        "title": "Test App",
        "description": "A test application",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }

    with pytest.raises(Exception, match="GitHub API Error"):
        workflow.execute(idea_data)

    # Check for WorkflowFailed event
    calls = mock_bus.publish.call_args_list
    assert any(isinstance(call[0][0], WorkflowFailed) for call in calls)

    # Find the failed event
    failed_event = next(call[0][0] for call in calls if isinstance(call[0][0], WorkflowFailed))
    assert "GitHub API Error" in failed_event.error
