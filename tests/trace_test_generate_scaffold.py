import pytest
from pytest_mock import MockerFixture
from src.core.workflow import IdeaWorkflow
from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from typing import Any, Optional

@pytest.fixture
def mock_gemini(mocker: MockerFixture) -> GeminiClient:
    return mocker.create_autospec(GeminiClient, instance=True)

@pytest.fixture
def mock_github(mocker: MockerFixture) -> GitHubClient:
    return mocker.create_autospec(GitHubClient, instance=True)

@pytest.fixture
def mock_jules(mocker: MockerFixture) -> JulesClient:
    return mocker.create_autospec(JulesClient, instance=True)

@pytest.fixture
def workflow(mock_gemini: GeminiClient, mock_github: GitHubClient, mock_jules: JulesClient) -> IdeaWorkflow:
    return IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

@pytest.mark.parametrize("idea_data, scaffold_response, expected_error", [
    (
        {"title": "Test App", "description": "Desc", "slug": "test-app", "tech_stack": ["Python"], "features": ["Login"]},
        {"requirements": ["pytest"], "run_command": "make run", "files": [{"path": "main.py", "content": "print('hi')"}, {"path": "README.md", "content": "skip me"}]},
        None
    ), # Happy Path
    (
        {"title": "Empty App", "description": "Desc", "slug": "empty-app"},
        {"requirements": [], "run_command": "", "files": []},
        None
    ), # Edge Case: No files
    (
        {"title": "Error App", "description": "Desc", "slug": "error-app"},
        RuntimeError("Gemini Error"),
        RuntimeError
    ), # Error State
])
def test_generate_scaffold_behavior(
    mocker: MockerFixture,
    workflow: IdeaWorkflow,
    idea_data: dict[str, Any],
    scaffold_response: dict[str, Any] | Exception,
    expected_error: Optional[type[Exception]]
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # Patch build_readme because it is imported in src/core/workflow.py
    mock_build_readme = mocker.patch("src.core.workflow.build_readme", autospec=True)
    mock_build_readme.return_value = "# README Content"

    # Configure Gemini mock
    if isinstance(scaffold_response, Exception):
        workflow.gemini.generate_project_scaffold.side_effect = scaffold_response
    else:
        workflow.gemini.generate_project_scaffold.return_value = scaffold_response
        # Configure GitHub mock for file creation
        workflow.github.create_file.return_value = {"content": "ok"}
        workflow.github.create_files.return_value = {"files_created": 1}

    # 2. Execution & Validation
    username = "testuser"
    verbose = True

    if expected_error:
        with pytest.raises(expected_error):
            workflow._generate_scaffold(username, idea_data, verbose)
    else:
        workflow._generate_scaffold(username, idea_data, verbose)

        # Verify Gemini called
        workflow.gemini.generate_project_scaffold.assert_called_once_with(idea_data)

        # Verify build_readme called
        mock_build_readme.assert_called_once()

        # Verify README creation (First Commit)
        workflow.github.create_file.assert_called_once_with(
            owner=username,
            repo=idea_data['slug'],
            path="README.md",
            content="# README Content",
            message="Initial commit: Add README with project description"
        )

        # Verify other files creation (Second Commit)
        if isinstance(scaffold_response, dict):
            files = scaffold_response.get('files', [])
            requirements = scaffold_response.get('requirements', [])

            # Logic from _prepare_scaffold_files:
            # - Filter out README.md
            # - Add requirements.txt if present

            should_create_files = False
            for f in files:
                if f['path'].lower() != 'readme.md':
                    should_create_files = True
                    break

            if requirements:
                should_create_files = True

            if should_create_files:
                workflow.github.create_files.assert_called_once()
                # Verify args
                call_args = workflow.github.create_files.call_args
                assert call_args.kwargs['owner'] == username
                assert call_args.kwargs['repo'] == idea_data['slug']
                assert len(call_args.kwargs['files']) > 0
            else:
                workflow.github.create_files.assert_not_called()
