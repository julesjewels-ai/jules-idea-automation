"""Unit tests for the IdeaWorkflow core logic."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from src.core.interfaces import EventBus
from src.core.models import WorkflowResult
from src.core.workflow import IdeaWorkflow
from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient


@pytest.fixture
def idea_data() -> dict[str, Any]:
    """Return a standard idea_data dictionary for tests."""
    return {
        "title": "Test Idea",
        "description": "A description for the test idea.",
        "slug": "test-idea",
        "tech_stack": ["Python"],
        "features": ["Testing"],
        "category": "cli_tool",
    }


def test_execute_success(mocker: MockerFixture, idea_data: dict[str, Any]) -> None:
    """Test that a successful workflow calls all dependencies and returns the expected result."""
    github = MagicMock(spec=GitHubClient)
    gemini = MagicMock(spec=GeminiClient)
    jules = MagicMock(spec=JulesClient)
    event_bus = MagicMock(spec=EventBus)

    # Mock return values
    github.get_user.return_value = {"login": "testuser"}
    github.create_files.return_value = {"files_created": 3}
    gemini.generate_project_scaffold.return_value = {"files": [], "requirements": []}
    gemini.generate_feature_maps.return_value = {}
    jules.source_exists.return_value = True
    jules.create_session.return_value = {"id": "session_123", "url": "https://jules.google.com/session/123"}

    # Mock uuid4 to have a predictable event_id in assertions if needed,
    # but since EventBus.publish is called with objects, we can just assert types.
    workflow = IdeaWorkflow(github=github, gemini=gemini, jules=jules, event_bus=event_bus)

    result = workflow.execute(idea_data, private=True, timeout=10)

    # Assertions on Github Client
    github.get_user.assert_called_once()
    github.create_repo.assert_called_once_with(
        name="test-idea",
        description="A description for the test idea.",
        private=True,
    )
    github.create_file.assert_called_once()
    github.create_files.assert_called_once()

    # Assertions on Gemini Client
    gemini.generate_project_scaffold.assert_called_once_with(idea_data)
    gemini.generate_feature_maps.assert_called_once_with(idea_data, [])

    # Assertions on Jules Client
    jules.source_exists.assert_called()
    jules.create_session.assert_called_once_with(
        "sources/github/testuser/test-idea", "A description for the test idea."
    )

    # Assertions on EventBus
    assert event_bus.publish.call_count == 2

    # Check Result
    assert isinstance(result, WorkflowResult)
    assert result.repo_url == "https://github.com/testuser/test-idea"
    assert result.session_id == "session_123"
    assert result.session_url == "https://jules.google.com/session/123"
    assert result.idea.title == "Test Idea"


def test_execute_jules_failure_recovers_gracefully(mocker: MockerFixture, idea_data: dict[str, Any]) -> None:
    """Test that a failure in Jules API calls does not crash the workflow and returns a partial success."""
    github = MagicMock(spec=GitHubClient)
    gemini = MagicMock(spec=GeminiClient)
    jules = MagicMock(spec=JulesClient)
    event_bus = MagicMock(spec=EventBus)

    # Mock return values
    github.get_user.return_value = {"login": "testuser"}
    github.create_files.return_value = {"files_created": 3}
    gemini.generate_project_scaffold.return_value = {"files": [], "requirements": []}
    gemini.generate_feature_maps.return_value = {}

    # Simulate Jules API failure during session creation
    jules.source_exists.return_value = True
    jules.create_session.side_effect = Exception("Jules API Timeout")

    workflow = IdeaWorkflow(github=github, gemini=gemini, jules=jules, event_bus=event_bus)

    # Should not raise an exception
    result = workflow.execute(idea_data, private=True, timeout=10)

    # Assert that everything else was called normally
    github.get_user.assert_called_once()
    github.create_repo.assert_called_once()
    github.create_file.assert_called_once()
    github.create_files.assert_called_once()
    gemini.generate_project_scaffold.assert_called_once()

    # Jules should have been called and failed
    jules.source_exists.assert_called()
    jules.create_session.assert_called_once()

    # EventBus should still emit workflow completion
    assert event_bus.publish.call_count == 2

    # Check Result -> This is the crucial part: session details should be None, but repo_url should be intact
    assert isinstance(result, WorkflowResult)
    assert result.repo_url == "https://github.com/testuser/test-idea"
    assert result.session_id is None
    assert result.session_url is None
    assert result.idea.title == "Test Idea"
