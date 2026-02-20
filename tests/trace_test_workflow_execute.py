import pytest
from pytest_mock import MockerFixture
from typing import Any, Dict, Generator
from unittest.mock import MagicMock

from src.core.workflow import IdeaWorkflow
from src.core.models import WorkflowResult
from src.services.github import GitHubClient
from src.services.gemini import GeminiClient
from src.services.jules import JulesClient


@pytest.fixture
def mock_github(mocker: MockerFixture) -> MagicMock:
    """Mock for GitHubClient."""
    mock = mocker.create_autospec(GitHubClient, instance=True)
    mock.get_user.return_value = {"login": "testuser"}
    mock.create_repo.return_value = {"html_url": "https://github.com/testuser/test-idea"}
    mock.create_file.return_value = {"content": {"html_url": "https://github.com/..."}}
    mock.create_files.return_value = {"files_created": 5}
    return mock


@pytest.fixture
def mock_gemini(mocker: MockerFixture) -> MagicMock:
    """Mock for GeminiClient."""
    mock = mocker.create_autospec(GeminiClient, instance=True)
    mock.generate_project_scaffold.return_value = {
        "files": [
            {"path": "main.py", "content": "print('hello')"},
            {"path": "README.md", "content": "should be ignored"}
        ],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    return mock


@pytest.fixture
def mock_jules(mocker: MockerFixture) -> MagicMock:
    """Mock for JulesClient."""
    mock = mocker.create_autospec(JulesClient, instance=True)
    mock.source_exists.return_value = True
    mock.create_session.return_value = {"id": "session_123", "url": "https://jules.google.com/session/123"}
    return mock


@pytest.fixture
def idea_data() -> Dict[str, Any]:
    """Sample input data for the workflow."""
    return {
        "title": "Test Idea",
        "description": "A test description",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }


@pytest.mark.parametrize("scenario, expected_result", [
    ("happy_path", "success"),
    ("polling_timeout", "timeout"),
    ("github_error", Exception),
    ("empty_scaffold", "success"),
])
def test_workflow_execute(
    mocker: MockerFixture,
    mock_github: MagicMock,
    mock_gemini: MagicMock,
    mock_jules: MagicMock,
    idea_data: Dict[str, Any],
    scenario: str,
    expected_result: Any
) -> None:
    # 1. Setup Mocks & Patches
    # Patch external functions used in execute
    mock_build_readme = mocker.patch("src.core.workflow.build_readme", return_value="# README")
    mock_poll_until = mocker.patch("src.core.workflow.poll_until")
    mock_print_report = mocker.patch("src.core.workflow.print_workflow_report")

    # Configure behavior based on scenario
    if scenario == "happy_path":
        mock_poll_until.return_value = True
        # trigger on_poll callback for coverage
        def side_effect(**kwargs):
            if "on_poll" in kwargs:
                kwargs["on_poll"](10)
            return True
        mock_poll_until.side_effect = side_effect

    elif scenario == "polling_timeout":
        mock_poll_until.return_value = False

    elif scenario == "github_error":
        mock_github.create_repo.side_effect = Exception("GitHub API Error")

    elif scenario == "empty_scaffold":
        mock_poll_until.return_value = True
        mock_gemini.generate_project_scaffold.return_value = {"files": []}

    # Initialize Workflow with mocks
    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

    # 2. Execution & Validation
    if isinstance(expected_result, type) and issubclass(expected_result, Exception):
        with pytest.raises(expected_result):
            workflow.execute(idea_data, verbose=True)
    else:
        result = workflow.execute(idea_data, verbose=True)

        assert isinstance(result, WorkflowResult)
        assert result.idea.slug == idea_data["slug"]
        assert result.repo_url == f"https://github.com/testuser/{idea_data['slug']}"

        # Verify GitHub interactions
        mock_github.get_user.assert_called_once()
        mock_github.create_repo.assert_called_once_with(
            name=idea_data['slug'],
            description=idea_data['description'][:350],
            private=False
        )

        # Verify Gemini interactions
        mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)

        # Verify README generation and commit
        mock_build_readme.assert_called_once()
        mock_github.create_file.assert_called_once()

        # Verify Scaffold commit
        if scenario != "empty_scaffold":
            mock_github.create_files.assert_called_once()
        else:
            mock_github.create_files.assert_not_called()

        # Verify Jules interactions
        source_id = f"sources/github/testuser/{idea_data['slug']}"
        mock_poll_until.assert_called_once()

        if expected_result == "success":
            # In happy path, create_session should be called
            mock_jules.create_session.assert_called_once_with(source_id, idea_data['description'])
            assert result.session_id == "session_123"
            assert result.session_url == "https://jules.google.com/session/123"
            mock_print_report.assert_called_once()

        elif expected_result == "timeout":
            # In timeout path, create_session should NOT be called
            mock_jules.create_session.assert_not_called()
            assert result.session_id is None
            assert result.session_url is None
            # print_report is called even if session is None, based on code logic?
            # Let's check code:
            # if verbose: print_workflow_report(...)
            # Yes, it is called at the end regardless of session existence,
            # because result.session_id will be None.
            mock_print_report.assert_called_once()
