import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from typing import Any, Union, Type
from src.core.workflow import IdeaWorkflow
from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from src.utils.errors import GenerationError

@pytest.fixture
def mock_gemini(mocker: MockerFixture) -> MagicMock:
    return mocker.create_autospec(GeminiClient, instance=True)

@pytest.fixture
def mock_github(mocker: MockerFixture) -> MagicMock:
    return mocker.create_autospec(GitHubClient, instance=True)

@pytest.fixture
def mock_jules(mocker: MockerFixture) -> MagicMock:
    return mocker.create_autospec(JulesClient, instance=True)

@pytest.fixture
def mock_build_readme(mocker: MockerFixture) -> MagicMock:
    # Patch the function imported in src.core.workflow
    return mocker.patch("src.core.workflow.build_readme", return_value="# Mock README")

@pytest.fixture
def workflow(mock_gemini: MagicMock, mock_github: MagicMock, mock_jules: MagicMock) -> IdeaWorkflow:
    return IdeaWorkflow(gemini=mock_gemini, github=mock_github, jules=mock_jules)

@pytest.mark.parametrize("scaffold_result, expected_files_count, expected_error", [
    (
        # Happy Path: Standard scaffold with requirements and files
        {
            "requirements": ["req1"],
            "run_command": "run cmd",
            "files": [{"path": "main.py", "content": "print('hello')"}]
        },
        2, # main.py + requirements.txt
        None
    ),
    (
        # Edge Case: No files, empty requirements (only README created outside scaffold logic)
        {
            "requirements": [],
            "run_command": "",
            "files": []
        },
        0,
        None
    ),
    (
        # Error State: Gemini fails to generate scaffold
        GenerationError("Failed to generate"),
        0,
        GenerationError
    ),
])
def test_generate_scaffold_behavior(
    mocker: MockerFixture,
    workflow: IdeaWorkflow,
    mock_gemini: MagicMock,
    mock_github: MagicMock,
    mock_build_readme: MagicMock,
    scaffold_result: Union[dict[str, Any], Exception],
    expected_files_count: int,
    expected_error: Union[Type[Exception], None]
) -> None:
    # 1. Setup
    username = "testuser"
    idea_data = {
        "title": "Test Idea",
        "description": "Desc",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }

    if isinstance(scaffold_result, Exception):
        mock_gemini.generate_project_scaffold.side_effect = scaffold_result
    else:
        mock_gemini.generate_project_scaffold.return_value = scaffold_result
        # GitHub create_files returns a summary dict
        mock_github.create_files.return_value = {"files_created": expected_files_count}

    # 2. Execution & Validation
    if expected_error:
        with pytest.raises(expected_error):
            workflow._generate_scaffold(username, idea_data, verbose=False)

        # Verify Gemini called
        mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)
        # Verify GitHub NOT called (assuming Gemini fails first)
        mock_github.create_file.assert_not_called()
    else:
        result = workflow._generate_scaffold(username, idea_data, verbose=False)
        assert result is None

        # Verify Gemini called
        mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)

        # Verify README built
        mock_build_readme.assert_called_once()

        # Verify README created (first commit)
        mock_github.create_file.assert_called_once()
        call_args = mock_github.create_file.call_args
        assert call_args.kwargs['path'] == "README.md"
        assert call_args.kwargs['content'] == "# Mock README"
        assert call_args.kwargs['owner'] == username
        assert call_args.kwargs['repo'] == idea_data['slug']

        # Verify Scaffold created (second commit)
        if expected_files_count > 0:
            mock_github.create_files.assert_called_once()
            files_arg = mock_github.create_files.call_args.kwargs['files']
            assert len(files_arg) == expected_files_count
            assert mock_github.create_files.call_args.kwargs['owner'] == username
            assert mock_github.create_files.call_args.kwargs['repo'] == idea_data['slug']
        else:
            mock_github.create_files.assert_not_called()
