"""Tests for IdeaWorkflow events."""

from unittest.mock import Mock, ANY
import pytest
from src.core.workflow import IdeaWorkflow, WorkflowResult
from src.core.events import LocalEventBus, WorkflowStarted, StepStarted, StepCompleted, WorkflowCompleted
from src.core.models import IdeaResponse, ProjectScaffold

@pytest.fixture
def mock_github():
    mock = Mock()
    mock.get_user.return_value = {"login": "testuser"}
    mock.create_repo.return_value = {"html_url": "https://github.com/testuser/test-slug"}
    mock.create_file.return_value = {}
    mock.create_files.return_value = {"files_created": 5, "commit_sha": "abc1234"}
    return mock

@pytest.fixture
def mock_gemini():
    mock = Mock()
    mock.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    return mock

@pytest.fixture
def mock_jules():
    mock = Mock()
    mock.source_exists.return_value = True
    mock.create_session.return_value = {"id": "session-123", "url": "https://jules.google.com/session-123"}
    return mock

@pytest.fixture
def event_bus():
    return LocalEventBus()

@pytest.fixture
def event_listener():
    listener = Mock()
    # Mock the on_event method so we can track calls
    listener.on_event = Mock()
    return listener

def test_workflow_emits_events_success(mock_github, mock_gemini, mock_jules, event_bus, event_listener):
    # Setup
    event_bus.subscribe(event_listener)
    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules, event_bus=event_bus)

    idea_data = {
        "title": "Test Idea",
        "description": "Description",
        "slug": "test-slug",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }

    # Execute
    result = workflow.execute(idea_data, verbose=False)

    # Assert Result
    assert isinstance(result, WorkflowResult)
    assert result.repo_url == "https://github.com/testuser/test-slug"

    # Assert Events
    # 1. WorkflowStarted
    event_listener.on_event.assert_any_call(ANY)
    calls = event_listener.on_event.call_args_list

    # Check specific events in order (simplified check)
    event_names = [call.args[0].name for call in calls]

    expected_sequence = [
        "workflow_started",
        "step_started", # Create repo
        "repo_created",
        "step_completed",
        "step_started", # Generate scaffold
        "step_completed",
        "step_started", # Commit files (README)
        "step_started", # Commit scaffold
        "scaffold_generated",
        "step_completed", # Commit scaffold
        "step_started", # Wait indexing
        "step_completed", # Source found
        "step_started", # Create session
        "session_created",
        "step_completed",
        "workflow_completed"
    ]

    # Filter only expected events to avoid noise if any extra ones
    filtered_events = [name for name in event_names if name in expected_sequence]

    # We just check key milestones exist
    assert "workflow_started" in event_names
    assert "repo_created" in event_names
    assert "scaffold_generated" in event_names
    assert "session_created" in event_names
    assert "workflow_completed" in event_names

def test_workflow_emits_failure_event(mock_github, mock_gemini, mock_jules, event_bus, event_listener):
    # Setup failure in GitHub
    mock_github.create_repo.side_effect = Exception("GitHub API Error")

    event_bus.subscribe(event_listener)
    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules, event_bus=event_bus)

    idea_data = {
        "title": "Test Idea",
        "description": "Description",
        "slug": "test-slug"
    }

    # Execute and Assert Exception
    with pytest.raises(Exception):
        workflow.execute(idea_data, verbose=False)

    # Assert Events
    calls = event_listener.on_event.call_args_list
    event_names = [call.args[0].name for call in calls]

    assert "workflow_started" in event_names
    assert "workflow_failed" in event_names
    assert "workflow_completed" not in event_names
