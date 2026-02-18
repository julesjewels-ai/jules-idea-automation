import pytest
from pytest_mock import MockerFixture
from src.core.workflow import IdeaWorkflow, WorkflowResult
from src.services.github import GitHubClient
from src.services.gemini import GeminiClient
from src.services.jules import JulesClient
from typing import Any, Dict, Type, Union

@pytest.fixture
def mock_github(mocker: MockerFixture) -> GitHubClient:
    mock = mocker.create_autospec(GitHubClient, instance=True)
    mock.get_user.return_value = {"login": "testuser"}
    mock.create_files.return_value = {"files_created": 2}
    return mock

@pytest.fixture
def mock_gemini(mocker: MockerFixture) -> GeminiClient:
    mock = mocker.create_autospec(GeminiClient, instance=True)
    mock.generate_project_scaffold.return_value = {
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "requirements": ["requests"],
        "run_command": "python main.py"
    }
    return mock

@pytest.fixture
def mock_jules(mocker: MockerFixture) -> JulesClient:
    mock = mocker.create_autospec(JulesClient, instance=True)
    mock.create_session.return_value = {"id": "session-123", "url": "http://jules/session"}
    # Mock source_exists is used in lambda in poll_until, but poll_until is mocked out.
    # So we don't strictly need to mock source_exists return value unless we test the lambda.
    # But since poll_until is mocked, the lambda is never executed by the real poll_until.
    return mock

@pytest.fixture
def idea_data() -> Dict[str, Any]:
    return {
        "title": "Test Idea",
        "description": "A test idea description",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }

@pytest.mark.parametrize("scenario, expected_result", [
    ("success", "success"),
    ("timeout", "timeout"),
    ("github_error", Exception),
    ("no_files", "success"),
    ("readme_skip", "success"),
])
def test_workflow_execute(
    mocker: MockerFixture,
    mock_github: GitHubClient,
    mock_gemini: GeminiClient,
    mock_jules: JulesClient,
    idea_data: Dict[str, Any],
    scenario: str,
    expected_result: Union[str, Type[Exception]]
) -> None:
    # 1. Setup Patches
    # Patch direct imports in src.core.workflow
    mock_poll = mocker.patch("src.core.workflow.poll_until")
    mock_build_readme = mocker.patch("src.core.workflow.build_readme", return_value="# README")
    mock_print_report = mocker.patch("src.core.workflow.print_workflow_report")

    # Configure Scenario
    if scenario == "success":
        # Simulate polling callback execution for coverage
        def poll_side_effect(condition, timeout, interval, on_poll=None):
            if on_poll:
                on_poll(10)
            return True
        mock_poll.side_effect = poll_side_effect
    elif scenario == "timeout":
        mock_poll.return_value = False
    elif scenario == "github_error":
        mock_github.create_repo.side_effect = Exception("GitHub Error")
    elif scenario == "no_files":
        mock_gemini.generate_project_scaffold.return_value = {"files": [], "requirements": []}
        mock_poll.return_value = True
    elif scenario == "readme_skip":
        mock_gemini.generate_project_scaffold.return_value = {
            "files": [
                {"path": "README.md", "content": "# Readme"},
                {"path": "main.py", "content": "print('hello')"}
            ],
            "requirements": ["requests"]
        }
        mock_poll.return_value = True

    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

    # 2. Execution & Validation
    if isinstance(expected_result, type) and issubclass(expected_result, Exception):
        with pytest.raises(expected_result):
            workflow.execute(idea_data, verbose=False)
    else:
        # Use verbose=True for coverage on success/timeout
        result = workflow.execute(idea_data, verbose=True)

        # Verify Core Logic
        mock_github.get_user.assert_called_once()
        mock_github.create_repo.assert_called_once_with(
            name=idea_data["slug"],
            description=idea_data["description"][:350],
            private=False
        )
        mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)
        mock_build_readme.assert_called_once()

        # Verify Git Commit Logic
        mock_github.create_file.assert_called_once() # README

        if scenario == "no_files":
            mock_github.create_files.assert_not_called()
        elif scenario == "readme_skip":
            mock_github.create_files.assert_called_once()
            # Verify only non-README files are created + requirements
            args = mock_github.create_files.call_args[1]
            created_files = args['files']
            paths = [f['path'] for f in created_files]
            assert "README.md" not in paths
            assert "main.py" in paths
            assert "requirements.txt" in paths
        else:
            mock_github.create_files.assert_called_once() # Scaffold

        # Verify Polling
        mock_poll.assert_called_once()

        # Verify Result
        assert isinstance(result, WorkflowResult)
        assert result.repo_url == f"https://github.com/testuser/{idea_data['slug']}"

        if scenario in ["success", "no_files", "readme_skip"]:
            mock_jules.create_session.assert_called_once()
            assert result.session_id == "session-123"
        elif scenario == "timeout":
            mock_jules.create_session.assert_not_called()
            assert result.session_id is None
