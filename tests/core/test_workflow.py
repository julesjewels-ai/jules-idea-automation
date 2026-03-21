"""Tests for IdeaWorkflow."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.core.workflow import IdeaWorkflow
from src.services.bus import NullEventBus


@pytest.fixture
def mock_github() -> MagicMock:
    """Mock GitHubClient."""
    mock = MagicMock()
    mock.get_user.return_value = {"login": "testuser"}
    mock.create_repo.return_value = {"html_url": "https://github.com/testuser/test-slug"}
    mock.create_file.return_value = {}
    mock.create_files.return_value = {"files_created": 5}
    return mock


@pytest.fixture
def mock_gemini() -> MagicMock:
    """Mock GeminiClient."""
    mock = MagicMock()
    mock.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py",
    }
    mock.generate_feature_maps.return_value = {
        "mvp_features": [{"name": "Auth", "priority": "P0"}],
        "production_features": [{"name": "Metrics", "priority": "P2"}],
    }
    return mock


@pytest.fixture
def idea_data() -> dict[str, Any]:
    """Test idea data."""
    return {
        "title": "Test Idea",
        "description": "A great idea.",
        "slug": "test-slug",
        "tech_stack": ["Python"],
        "features": ["Auth"],
    }


def test_execute_jules_failure_graceful_recovery(
    mock_github: MagicMock,
    mock_gemini: MagicMock,
    idea_data: dict[str, Any],
) -> None:
    """Test that workflow completes partially when Jules session creation fails."""
    mock_jules = MagicMock()
    # Simulate Jules exception
    mock_jules.source_exists.side_effect = Exception("API Timeout")

    workflow = IdeaWorkflow(
        github=mock_github,
        gemini=mock_gemini,
        jules=mock_jules,
        event_bus=NullEventBus(),
    )

    result = workflow.execute(idea_data, private=True, timeout=1)

    # Repository was created
    mock_github.create_repo.assert_called_once()
    assert result.repo_url == "https://github.com/testuser/test-slug"

    # Jules session failed but exception was caught
    assert result.session_id is None
    assert result.session_url is None


def test_execute_happy_path(
    mock_github: MagicMock,
    mock_gemini: MagicMock,
    idea_data: dict[str, Any],
) -> None:
    """Test full workflow happy path."""
    mock_jules = MagicMock()
    mock_jules.source_exists.return_value = True
    mock_jules.create_session.return_value = {"id": "123", "url": "https://jules.google.com/sessions/123"}

    workflow = IdeaWorkflow(
        github=mock_github,
        gemini=mock_gemini,
        jules=mock_jules,
        event_bus=NullEventBus(),
    )

    result = workflow.execute(idea_data, private=True, timeout=1)

    assert result.repo_url == "https://github.com/testuser/test-slug"
    assert result.session_id == "123"
    assert result.session_url == "https://jules.google.com/sessions/123"
