"""Trace suite for IdeaWorkflow.execute behavior."""

from __future__ import annotations

import pytest
from unittest.mock import Mock
from pytest_mock import MockerFixture
from typing import Any

from src.core.workflow import IdeaWorkflow
from src.core.models import WorkflowResult
from src.services.github import GitHubClient
from src.services.gemini import GeminiClient
from src.services.jules import JulesClient


@pytest.fixture
def mock_clients(mocker: MockerFixture) -> dict[str, Mock]:
    """Create isolated mock clients."""
    return {
        "github": mocker.create_autospec(GitHubClient, instance=True),
        "gemini": mocker.create_autospec(GeminiClient, instance=True),
        "jules": mocker.create_autospec(JulesClient, instance=True),
    }


@pytest.fixture
def idea_data() -> dict[str, Any]:
    """Sample idea data matching IdeaResponse schema."""
    return {
        "title": "Test App",
        "slug": "test-app",
        "description": "A test application",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }


@pytest.mark.parametrize("scenario, mocks_config, expected", [
    (
        "happy_path",
        {
            "poll_result": True,
            "session_data": {"id": "sess_123", "url": "http://jules/s/123"}
        },
        "success"
    ),
    (
        "jules_timeout",
        {
            "poll_result": False,
            "session_data": None
        },
        "timeout"
    ),
    (
        "github_error",
        {
            "github_exception": RuntimeError("GitHub API Error")
        },
        RuntimeError
    ),
])
def test_execute_behavior(
    mocker: MockerFixture,
    mock_clients: dict[str, Mock],
    idea_data: dict[str, Any],
    scenario: str,
    mocks_config: dict[str, Any],
    expected: str | type[Exception]
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # Patch dependencies imported in src.core.workflow
    mock_poll = mocker.patch("src.core.workflow.poll_until")
    mocker.patch("src.core.workflow.build_readme", return_value="# README")
    mocker.patch("src.core.workflow.print_workflow_report")

    # Configure injected clients
    gh = mock_clients["github"]
    gem = mock_clients["gemini"]
    jules = mock_clients["jules"]

    # Common setup
    gh.get_user.return_value = {"login": "testuser"}
    gem.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }

    # Scenario-specific configuration
    if scenario == "github_error":
        gh.create_repo.side_effect = mocks_config["github_exception"]
    else:
        gh.create_repo.return_value = None
        gh.create_file.return_value = {"content": "readme"}
        gh.create_files.return_value = {"files_created": 1}

        mock_poll.return_value = mocks_config["poll_result"]
        if mocks_config.get("session_data"):
            jules.create_session.return_value = mocks_config["session_data"]

    # Initialize Workflow with injected mocks
    workflow = IdeaWorkflow(github=gh, gemini=gem, jules=jules)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            workflow.execute(idea_data, verbose=False)

        # Verify call stop at error
        gh.create_repo.assert_called_once()
        gem.generate_project_scaffold.assert_not_called()

    else:
        result = workflow.execute(idea_data, verbose=False)

        # Verify Core Logic
        assert isinstance(result, WorkflowResult)
        assert result.repo_url == "https://github.com/testuser/test-app"

        # Verify Side Effects
        gh.get_user.assert_called_once()
        gh.create_repo.assert_called_once_with(
            name="test-app",
            description="A test application",
            private=True
        )
        gem.generate_project_scaffold.assert_called_once_with(idea_data)

        # Verify Scaffold Commit
        gh.create_file.assert_called_once()  # README
        gh.create_files.assert_called_once()  # Scaffold files

        # Verify Jules Logic
        mock_poll.assert_called_once()

        if expected == "success":
            jules.create_session.assert_called_once()
            assert result.session_id == "sess_123"
        elif expected == "timeout":
            jules.create_session.assert_not_called()
            assert result.session_id is None
