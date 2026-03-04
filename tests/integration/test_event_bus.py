"""Integration tests for Event Bus and Audit Logging."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from src.core.events import WorkflowCompleted, WorkflowStarted
from src.core.workflow import IdeaWorkflow
from src.services.audit import JsonFileAuditLogger
from src.services.bus import LocalEventBus


def test_event_bus_audit_integration(tmp_path: Path) -> None:
    """Test that executing a workflow publishes events that are written to a log file."""
    # Setup
    log_file = tmp_path / "test_audit.jsonl"
    event_bus = LocalEventBus()
    audit_logger = JsonFileAuditLogger(log_file=str(log_file))

    event_bus.subscribe(WorkflowStarted, audit_logger)
    event_bus.subscribe(WorkflowCompleted, audit_logger)

    # Mock dependencies for the workflow
    mock_github = MagicMock()
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_repo.return_value = None
    mock_github.create_file.return_value = None
    mock_github.create_files.return_value = {"files_created": 1}

    mock_gemini = MagicMock()
    mock_gemini.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py",
    }

    mock_jules = MagicMock()
    mock_jules.source_exists.return_value = True
    mock_jules.create_session.return_value = {"id": "session-123", "url": "http://example.com"}

    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules, event_bus=event_bus)

    idea_data = {
        "title": "Test Idea",
        "description": "A test description",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature 1"],
        "category": "cli_tool",
    }

    # Execute workflow
    workflow.execute(idea_data, verbose=False)

    # Verify log file was created and contains expected entries
    assert log_file.exists()

    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 2

    # Parse the logged events
    event1 = json.loads(lines[0])
    event2 = json.loads(lines[1])

    assert event1["event_type"] == "WorkflowStarted"
    assert event1["idea_title"] == "Test Idea"
    assert event1["idea_slug"] == "test-idea"
    assert event1["category"] == "cli_tool"
    assert "event_id" in event1
    assert "timestamp" in event1

    assert event2["event_type"] == "WorkflowCompleted"
    assert event2["idea_title"] == "Test Idea"
    assert event2["idea_slug"] == "test-idea"
    assert event2["repo_url"] == "https://github.com/testuser/test-idea"
    assert event2["session_id"] == "session-123"
    assert "event_id" in event2
    assert "timestamp" in event2
