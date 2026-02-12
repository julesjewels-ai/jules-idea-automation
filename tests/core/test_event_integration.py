"""Integration tests for the Event System."""

from unittest.mock import Mock
from src.core.workflow import IdeaWorkflow
from src.core.events import (
    LocalEventBus,
    Event,
    WorkflowStarted,
    StepStarted,
    StepCompleted,
    WorkflowCompleted
)


class MockListener:
    """A simple listener for testing purposes."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


def test_workflow_events_flow() -> None:
    """Test that the workflow emits the expected sequence of events."""
    # Mock external services
    mock_github = Mock()
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": 5}

    mock_gemini = Mock()
    mock_gemini.generate_project_scaffold.return_value = {
        "files": [{
            "path": "main.py",
            "content": "print('hello')",
            "description": "Main file"
        }],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }

    mock_jules = Mock()
    mock_jules.source_exists.return_value = True
    mock_jules.create_session.return_value = {
        "id": "session-123",
        "url": "http://jules/s/123"
    }

    # Setup Event System
    bus = LocalEventBus()
    listener = MockListener()
    bus.subscribe(listener)

    # Setup Workflow
    workflow = IdeaWorkflow(
        github=mock_github,
        gemini=mock_gemini,
        jules=mock_jules,
        bus=bus
    )

    idea_data = {
        "title": "Test Idea",
        "description": "A test idea",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }

    # Execute
    workflow.execute(idea_data, verbose=False)

    # Verify Events
    event_types = [type(e) for e in listener.events]

    assert WorkflowStarted in event_types
    assert StepStarted in event_types
    assert StepCompleted in event_types
    assert WorkflowCompleted in event_types

    # Verify WorkflowStarted
    assert isinstance(listener.events[0], WorkflowStarted)
    assert listener.events[0].slug == "test-idea"

    # Verify Step Flow
    step_names = [
        e.step_name for e in listener.events if isinstance(e, StepStarted)
    ]
    assert "Creating public GitHub repository 'test-idea'" in step_names
    assert "Generating MVP scaffold with Gemini" in step_names
    assert "Committing README and scaffold files" in step_names

    # Verify WorkflowCompleted
    assert isinstance(listener.events[-1], WorkflowCompleted)
    assert listener.events[-1].result.session_id == "session-123"
