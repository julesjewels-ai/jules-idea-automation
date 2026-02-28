import pytest
from pytest_mock import MockerFixture
from typing import Any

from src.core.workflow import IdeaWorkflow
from src.core.models import WorkflowResult

@pytest.fixture
def idea_data() -> dict[str, Any]:
    return {
        "title": "Test Idea",
        "description": "A descriptive test idea.",
        "slug": "test-idea",
        "tech_stack": ["Python", "Pytest"],
        "features": ["Testing"]
    }


@pytest.mark.parametrize("mock_jules_return, error_on_github, expected", [
    (
        {"id": "session-123", "url": "https://jules/session-123"},
        False,
        "success"
    ),
    (
        None,
        False,
        "timeout"
    ),
    (
        None,
        True,
        RuntimeError
    ),
])
def test_ideaworkflow_execute(
    mocker: MockerFixture,
    idea_data: dict[str, Any],
    mock_jules_return: dict[str, Any] | None,
    error_on_github: bool,
    expected: str | type[Exception]
) -> None:
    # 1. Setup Namespace Isolated Mocks

    # We mock the external dependencies so the class instantiates without real clients
    mock_github_client_cls = mocker.patch("src.core.workflow.GitHubClient", autospec=True)
    mock_gemini_client_cls = mocker.patch("src.core.workflow.GeminiClient", autospec=True)
    mock_jules_client_cls = mocker.patch("src.core.workflow.JulesClient", autospec=True)

    # Additional mocks for internal dependencies in workflow.py
    mocker.patch("src.core.workflow.build_readme", autospec=True, return_value="README content")
    mock_poll = mocker.patch("src.core.workflow.poll_until", autospec=True)

    # Mock print to avoid side effects
    mocker.patch("builtins.print")
    # Mock the reporter (imported via `from src.utils.reporter import print_workflow_report`
    # so we mock it where it is used, which is src.core.workflow)
    mock_print_report = mocker.patch("src.core.workflow.print_workflow_report", autospec=True)

    workflow = IdeaWorkflow(
        github=mock_github_client_cls.return_value,
        gemini=mock_gemini_client_cls.return_value,
        jules=mock_jules_client_cls.return_value
    )

    from unittest.mock import MagicMock

    # Ensure our injected mocks are treated as MagicMocks for type checking
    mock_github: MagicMock = workflow.github  # type: ignore[assignment]
    mock_gemini: MagicMock = workflow.gemini  # type: ignore[assignment]
    mock_jules: MagicMock = workflow.jules    # type: ignore[assignment]

    # Setup the injected mocks behavior
    if error_on_github:
        mock_github.get_user.side_effect = RuntimeError("GitHub Error")
    else:
        mock_github.get_user.return_value = {"login": "testuser"}

    mock_gemini.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    mock_github.create_files.return_value = {"files_created": 2}

    if mock_jules_return is None and expected == "timeout":
        mock_poll.return_value = False
        mock_jules.create_session.return_value = None
    else:
        mock_poll.return_value = True
        mock_jules.create_session.return_value = mock_jules_return

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            workflow.execute(idea_data, private=True, timeout=1800, verbose=True)
    else:
        result = workflow.execute(idea_data, private=True, timeout=1800, verbose=True)

        # Verify side effects on dependencies
        mock_github.get_user.assert_called_once()
        mock_github.create_repo.assert_called_once_with(
            name=idea_data["slug"],
            description=idea_data["description"][:350],
            private=True
        )
        mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)
        mock_poll.assert_called_once()
        mock_print_report.assert_called_once()

        # Verify return value
        assert isinstance(result, WorkflowResult)
        assert result.repo_url == f"https://github.com/testuser/{idea_data['slug']}"
        assert result.idea.title == idea_data["title"]

        if expected == "success":
            mock_jules.create_session.assert_called_once()
            assert mock_jules_return is not None
            assert result.session_id == mock_jules_return["id"]
            assert result.session_url == mock_jules_return["url"]
        elif expected == "timeout":
            mock_jules.create_session.assert_not_called()
            assert result.session_id is None
            assert result.session_url is None
