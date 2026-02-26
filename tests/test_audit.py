"""Integration tests for the Audit Logging feature."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.events import (
    WorkflowStarted,
    RepoCreated,
    ScaffoldGenerated,
    SessionCreated,
    WorkflowCompleted
)
from src.services.bus import InMemoryEventBus
from src.services.audit import JsonFileAuditLogger
from src.core.workflow import IdeaWorkflow
from src.core.models import WorkflowResult, IdeaResponse


@pytest.fixture
def temp_audit_file(tmp_path):
    """Fixture providing a temporary path for the audit log."""
    return tmp_path / "audit_test.jsonl"


def test_audit_logger_writes_events(temp_audit_file):
    """Test that the audit logger writes events to the file."""
    bus = InMemoryEventBus()
    logger = JsonFileAuditLogger(filepath=str(temp_audit_file))
    bus.subscribe(logger)

    event = WorkflowStarted(
        idea_title="Test Idea",
        idea_slug="test-idea",
        workflow_params={"private": True}
    )

    bus.publish(event)

    assert temp_audit_file.exists()
    content = temp_audit_file.read_text()
    data = json.loads(content)

    assert data["event_type"] == "workflow_started"
    assert data["idea_title"] == "Test Idea"
    assert "timestamp" in data


def test_workflow_publishes_events(temp_audit_file):
    """Test that the workflow publishes events that get logged."""

    # Setup mocks
    mock_github = MagicMock()
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": 5}

    mock_gemini = MagicMock()
    mock_gemini.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }

    mock_jules = MagicMock()
    mock_jules.source_exists.return_value = True
    mock_jules.create_session.return_value = {
        "id": "123",
        "name": "projects/123/locations/us-central1/sessions/456",
        "url": "https://jules.google.com/session/456"
    }

    # Setup Event Bus & Logger
    bus = InMemoryEventBus()
    logger = JsonFileAuditLogger(filepath=str(temp_audit_file))
    bus.subscribe(logger)

    # Initialize Workflow
    workflow = IdeaWorkflow(
        github=mock_github,
        gemini=mock_gemini,
        jules=mock_jules,
        event_bus=bus
    )

    idea_data = {
        "title": "Test App",
        "description": "A test app",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["cli"]
    }

    # Execute
    with patch("src.core.workflow.print_workflow_report"): # Suppress report output
        workflow.execute(idea_data, verbose=False)

    # Verify Log Content
    log_lines = temp_audit_file.read_text().strip().split('\n')
    events = [json.loads(line) for line in log_lines]

    event_types = [e["event_type"] for e in events]

    assert "workflow_started" in event_types
    assert "repo_created" in event_types
    assert "scaffold_generated" in event_types
    assert "session_created" in event_types
    assert "workflow_completed" in event_types

    # Check specific event data
    repo_event = next(e for e in events if e["event_type"] == "repo_created")
    assert repo_event["repo_url"] == "https://github.com/testuser/test-app"

    scaffold_event = next(e for e in events if e["event_type"] == "scaffold_generated")
    assert scaffold_event["file_count"] == 5
