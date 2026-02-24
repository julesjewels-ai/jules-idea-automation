import pytest
from pytest_mock import MockerFixture
from unittest.mock import Mock
from typing import Any, Callable

from src.core.workflow import IdeaWorkflow
from src.services.github import GitHubClient
from src.services.gemini import GeminiClient
from src.services.jules import JulesClient


@pytest.fixture
def mock_github(mocker: MockerFixture) -> Mock:
    mock = mocker.create_autospec(GitHubClient, instance=True)
    mock.get_user.return_value = {"login": "testuser"}
    mock.create_repo.return_value = {"html_url": "https://github.com/testuser/test-slug"}
    mock.create_file.return_value = {"content": {"name": "README.md"}}
    mock.create_files.return_value = {"files_created": 2}
    return mock


@pytest.fixture
def mock_gemini(mocker: MockerFixture) -> Mock:
    mock = mocker.create_autospec(GeminiClient, instance=True)
    mock.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    return mock


@pytest.fixture
def mock_jules(mocker: MockerFixture) -> Mock:
    mock = mocker.create_autospec(JulesClient, instance=True)
    mock.source_exists.return_value = True
    mock.create_session.return_value = {
        "id": "session123",
        "url": "https://jules.google.com/sessions/session123"
    }
    return mock


@pytest.fixture
def mock_poll_until(mocker: MockerFixture) -> Mock:
    return mocker.patch("src.core.workflow.poll_until", return_value=True)


@pytest.fixture
def mock_print_report(mocker: MockerFixture) -> Mock:
    return mocker.patch("src.core.workflow.print_workflow_report")


@pytest.fixture
def mock_build_readme(mocker: MockerFixture) -> Mock:
    return mocker.patch("src.core.workflow.build_readme", return_value="# Readme")


@pytest.fixture
def workflow(mock_github: Mock, mock_gemini: Mock, mock_jules: Mock) -> IdeaWorkflow:
    return IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)


@pytest.fixture
def idea_data() -> dict[str, Any]:
    return {
        "title": "Test Idea",
        "description": "A test description",
        "slug": "test-slug",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }


def setup_happy_path(m_gh: Mock, m_gem: Mock, m_jul: Mock, m_poll: Mock) -> None:
    pass


def setup_jules_timeout(m_gh: Mock, m_gem: Mock, m_jul: Mock, m_poll: Mock) -> None:
    m_poll.return_value = False


def setup_empty_scaffold(m_gh: Mock, m_gem: Mock, m_jul: Mock, m_poll: Mock) -> None:
    m_gem.generate_project_scaffold.return_value = {"files": [], "requirements": []}


def setup_github_error(m_gh: Mock, m_gem: Mock, m_jul: Mock, m_poll: Mock) -> None:
    m_gh.create_repo.side_effect = RuntimeError("GitHub API Error")


@pytest.mark.parametrize("scenario, setup_func, expected_result", [
    ("happy_path", setup_happy_path, "success"),
    ("jules_timeout", setup_jules_timeout, "no_session"),
    ("empty_scaffold", setup_empty_scaffold, "no_files_created"),
    ("github_error", setup_github_error, RuntimeError),
])
def test_workflow_execute(
    mocker: MockerFixture,
    workflow: IdeaWorkflow,
    mock_github: Mock,
    mock_gemini: Mock,
    mock_jules: Mock,
    mock_poll_until: Mock,
    mock_print_report: Mock,
    mock_build_readme: Mock,
    idea_data: dict[str, Any],
    scenario: str,
    setup_func: Callable[..., None],
    expected_result: Any
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    setup_func(mock_github, mock_gemini, mock_jules, mock_poll_until)

    # 2. Execution & Validation
    if isinstance(expected_result, type) and issubclass(expected_result, Exception):
        with pytest.raises(expected_result):
            workflow.execute(idea_data, verbose=True)
    else:
        result = workflow.execute(idea_data, verbose=True)

        # Verify return value
        assert result.idea.slug == idea_data["slug"]
        assert result.repo_url == f"https://github.com/testuser/{idea_data['slug']}"

        # Verify Side Effects
        mock_github.get_user.assert_called_once()
        mock_github.create_repo.assert_called_once_with(
            name=idea_data["slug"],
            description=idea_data["description"][:350],
            private=True
        )

        if expected_result == "success":
            assert result.session_id == "session123"

            # Verify README creation
            mock_build_readme.assert_called_once()
            mock_github.create_file.assert_called_once()
            assert mock_github.create_file.call_args[1]["path"] == "README.md"

            # Verify Scaffold creation
            mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)
            mock_github.create_files.assert_called_once()
            created_files = mock_github.create_files.call_args[1]["files"]
            assert len(created_files) == 2  # main.py + requirements.txt
            assert any(f["path"] == "main.py" for f in created_files)
            assert any(f["path"] == "requirements.txt" for f in created_files)

            # Verify Jules interaction
            mock_poll_until.assert_called_once()
            mock_jules.create_session.assert_called_once()
            mock_print_report.assert_called_once()

        elif expected_result == "no_session":
            assert result.session_id is None
            mock_poll_until.assert_called_once()
            mock_jules.create_session.assert_not_called()

        elif expected_result == "no_files_created":
            mock_gemini.generate_project_scaffold.assert_called_once()
            mock_github.create_files.assert_not_called()
            # README should still be created
            mock_github.create_file.assert_called_once()
