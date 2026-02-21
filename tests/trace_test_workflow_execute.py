"""Trace test for IdeaWorkflow.execute."""

import pytest
from unittest.mock import Mock
from pytest_mock import MockerFixture
from typing import Any, Dict, Optional

from src.core.workflow import IdeaWorkflow, WorkflowResult


@pytest.fixture
def mock_github(mocker: MockerFixture) -> Mock:
    """Mock GitHubClient."""
    mock = mocker.Mock()
    mock.get_user.return_value = {"login": "testuser"}
    mock.create_repo.return_value = None
    mock.create_file.return_value = None
    mock.create_files.return_value = {"files_created": 2}
    return mock


@pytest.fixture
def mock_gemini(mocker: MockerFixture) -> Mock:
    """Mock GeminiClient."""
    mock = mocker.Mock()
    mock.generate_project_scaffold.return_value = {
        "files": [
            {"path": "main.py", "content": "print('hello')"},
            {"path": "README.md", "content": "should be skipped"}
        ],
        "requirements": ["requests"],
        "run_command": "python main.py"
    }
    return mock


@pytest.fixture
def mock_jules(mocker: MockerFixture) -> Mock:
    """Mock JulesClient."""
    mock = mocker.Mock()
    mock.source_exists.return_value = True
    mock.create_session.return_value = {"id": "sess-123", "url": "http://jules/s/123"}
    return mock


@pytest.fixture
def idea_data() -> Dict[str, Any]:
    """Sample idea data."""
    return {
        "title": "Test App",
        "description": "A test application",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["cli"]
    }


@pytest.mark.parametrize("scenario, poll_result, expected_session_call, expected_error", [
    (
        "happy_path",
        True,
        True,
        None
    ),
    (
        "poll_timeout",
        False,
        False,
        None
    ),
    (
        "github_error",
        True,
        False,
        RuntimeError("GitHub API Error")
    )
])
def test_execute_behavior(
    mocker: MockerFixture,
    mock_github: Mock,
    mock_gemini: Mock,
    mock_jules: Mock,
    idea_data: Dict[str, Any],
    scenario: str,
    poll_result: bool,
    expected_session_call: bool,
    expected_error: Optional[Exception]
) -> None:
    """Test IdeaWorkflow.execute behavior.

    Covers:
    - Happy Path: Successful execution.
    - Edge Case: Polling timeout (Jules source not found).
    - Error State: Exception during execution.
    """
    # 1. Setup Mocks (Namespace Verified)
    # Patch imported functions in src.core.workflow
    mock_poll = mocker.patch("src.core.workflow.poll_until", return_value=poll_result)
    mock_build_readme = mocker.patch("src.core.workflow.build_readme", return_value="# Mock Readme")
    mock_print_report = mocker.patch("src.core.workflow.print_workflow_report")

    # Setup specific error conditions
    if scenario == "github_error":
        mock_github.create_repo.side_effect = expected_error

    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

    # 2. Execution & Validation
    if expected_error:
        with pytest.raises(type(expected_error), match=str(expected_error)):
            workflow.execute(idea_data)
        return

    result = workflow.execute(idea_data, verbose=True)

    # Verify Result
    assert isinstance(result, WorkflowResult)
    assert result.repo_url == "https://github.com/testuser/test-app"
    assert result.idea.title == idea_data["title"]

    # Verify GitHub Interactions
    mock_github.get_user.assert_called_once()
    mock_github.create_repo.assert_called_once_with(
        name="test-app",
        description="A test application",
        private=True
    )

    # Verify Scaffold Generation
    mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)

    # Verify README creation
    mock_build_readme.assert_called_once()
    mock_github.create_file.assert_called_once_with(
        owner="testuser",
        repo="test-app",
        path="README.md",
        content="# Mock Readme",
        message="Initial commit: Add README with project description"
    )

    # Verify Scaffold Files Creation
    # Note: verify that 'README.md' from scaffold was filtered out and requirements.txt added
    expected_files = [
        {'path': 'main.py', 'content': "print('hello')"},
        {'path': 'requirements.txt', 'content': 'requests'}
    ]
    mock_github.create_files.assert_called_once_with(
        owner="testuser",
        repo="test-app",
        files=expected_files,
        message="feat: Add MVP scaffold with SOLID structure"
    )

    # Verify Polling
    mock_poll.assert_called_once()
    # Inspect the condition lambda passed to poll_until
    poll_kwargs = mock_poll.call_args[1] if mock_poll.call_args else {}
    condition_func = poll_kwargs.get("condition") or mock_poll.call_args[0][0]
    assert callable(condition_func)

    # Execute the condition lambda to verify it calls jules.source_exists
    condition_func()
    mock_jules.source_exists.assert_called_with("sources/github/testuser/test-app")

    # Verify Session Creation
    if expected_session_call:
        mock_jules.create_session.assert_called_once_with(
            "sources/github/testuser/test-app",
            "A test application"
        )
        assert result.session_id == "sess-123"
        assert result.session_url == "http://jules/s/123"
        mock_print_report.assert_called_once()
    else:
        mock_jules.create_session.assert_not_called()
        assert result.session_id is None
        assert result.session_url is None
