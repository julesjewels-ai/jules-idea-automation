from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from src.core.models import WorkflowResult
from src.core.workflow import IdeaWorkflow
from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient


@pytest.fixture
def mock_clients(mocker: MockerFixture) -> dict[str, MagicMock]:
    return {
        "github": mocker.create_autospec(GitHubClient, instance=True),
        "gemini": mocker.create_autospec(GeminiClient, instance=True),
        "jules": mocker.create_autospec(JulesClient, instance=True),
    }


@pytest.fixture
def idea_data() -> dict[str, Any]:
    return {
        "title": "Test Idea",
        "description": "A test description",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"],
    }


@pytest.mark.parametrize(
    "scenario, private_flag, verbose_flag, poll_success, expected_result",
    [
        ("happy_path", True, True, True, "success"),
        ("public_repo_quiet", False, False, True, "success"),
        ("jules_timeout", True, True, False, "timeout_error"),
    ],
)
def test_execute_behavior(
    mocker: MockerFixture,
    mock_clients: dict[str, MagicMock],
    idea_data: dict[str, Any],
    scenario: str,
    private_flag: bool,
    verbose_flag: bool,
    poll_success: bool,
    expected_result: str,
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # Patch imported functions in src.core.workflow
    mock_poll = mocker.patch("src.core.workflow.poll_until")
    mock_build_readme = mocker.patch("src.core.workflow.build_readme")
    mock_report = mocker.patch("src.core.workflow.print_workflow_report")

    # Configure injected mocks
    github = mock_clients["github"]
    gemini = mock_clients["gemini"]
    jules = mock_clients["jules"]

    github.get_user.return_value = {"login": "testuser"}
    gemini.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')", "description": "Main file"}],
        "requirements": ["requests"],
        "run_command": "python main.py",
    }
    mock_build_readme.return_value = "# README"

    # Configure poll result
    mock_poll.return_value = poll_success

    # Configure Jules session creation if poll succeeds
    if poll_success:
        jules.create_session.return_value = {"id": "session_123", "url": "http://session"}

    # Workflow instance
    workflow = IdeaWorkflow(github=github, gemini=gemini, jules=jules)

    # 2. Execution & Validation
    result = workflow.execute(idea_data, private=private_flag, timeout=10, verbose=verbose_flag)

    # Assert return type
    assert isinstance(result, WorkflowResult)
    assert result.repo_url == "https://github.com/testuser/test-idea"

    # Verify side effects
    github.get_user.assert_called()
    github.create_repo.assert_called_once_with(name="test-idea", description="A test description", private=private_flag)
    gemini.generate_project_scaffold.assert_called_once_with(idea_data)

    # Verify README creation
    github.create_file.assert_called_once()
    assert github.create_file.call_args[1]["path"] == "README.md"

    # Verify Scaffold creation
    github.create_files.assert_called_once()
    files_arg = github.create_files.call_args[1]["files"]
    assert len(files_arg) == 2  # main.py and requirements.txt
    assert files_arg[0]["path"] == "main.py"
    assert files_arg[1]["path"] == "requirements.txt"

    # Verify Polling
    mock_poll.assert_called_once()

    if expected_result == "success":
        assert result.session_id == "session_123"
        assert result.session_url == "http://session"
        jules.create_session.assert_called_once()
        if verbose_flag:
            mock_report.assert_called_once()
        else:
            mock_report.assert_not_called()

    elif expected_result == "timeout_error":
        assert result.session_id is None
        assert result.session_url is None
        jules.create_session.assert_not_called()
