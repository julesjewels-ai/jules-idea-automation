import pytest
from pytest_mock import MockerFixture
from src.core.workflow import IdeaWorkflow
from typing import Any, Optional

@pytest.fixture
def mock_gemini(mocker: MockerFixture):
    return mocker.Mock()

@pytest.fixture
def mock_github(mocker: MockerFixture):
    return mocker.Mock()

@pytest.fixture
def mock_jules(mocker: MockerFixture):
    return mocker.Mock()

@pytest.fixture
def workflow(mock_gemini, mock_github, mock_jules):
    return IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

@pytest.mark.parametrize("idea_data, scaffold_response, verbose, expected_create_files_count", [
    (
        # Happy Path: Files and requirements
        {
            "title": "Test App",
            "description": "A test app",
            "slug": "test-app",
            "tech_stack": ["python"],
            "features": ["login"]
        },
        {
            "files": [{"path": "main.py", "content": "print('hello')"}],
            "requirements": ["requests"],
            "run_command": "python main.py"
        },
        True,
        2  # 1 main.py + 1 requirements.txt
    ),
    (
        # Edge Case: No files, no requirements
        {
            "title": "Empty App",
            "description": "Empty",
            "slug": "empty-app"
        },
        {
            "files": [],
            "requirements": [],
            "run_command": ""
        },
        False,
        0
    ),
    (
        # Edge Case: README in files (should be filtered out)
        {
            "title": "Readme App",
            "description": "App with readme",
            "slug": "readme-app"
        },
        {
            "files": [
                {"path": "README.md", "content": "Duplicate"},
                {"path": "main.py", "content": "print('hello')"}
            ],
            "requirements": [],
            "run_command": ""
        },
        True,
        1  # Only main.py, README.md filtered out
    ),
    (
        # Error State: Gemini raises Exception
        {
            "title": "Error App",
            "description": "Error",
            "slug": "error-app"
        },
        RuntimeError("API Error"),
        False,
        0
    ),
])
def test_generate_scaffold_behavior(
    mocker: MockerFixture,
    workflow: IdeaWorkflow,
    mock_gemini: Any,
    mock_github: Any,
    idea_data: dict[str, Any],
    scaffold_response: Any,
    verbose: bool,
    expected_create_files_count: int
) -> None:
    # 1. Setup Mocks
    username = "testuser"
    mock_build_readme = mocker.patch("src.core.workflow.build_readme", return_value="# README")

    if isinstance(scaffold_response, Exception):
        mock_gemini.generate_project_scaffold.side_effect = scaffold_response

        # 2. Execution & Validation (Error Case)
        with pytest.raises(type(scaffold_response)):
             workflow._generate_scaffold(username, idea_data, verbose)

        # Verify Gemini called
        mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)

        # Verify no subsequent calls
        mock_build_readme.assert_not_called()
        mock_github.create_file.assert_not_called()
        mock_github.create_files.assert_not_called()
        return

    mock_gemini.generate_project_scaffold.return_value = scaffold_response
    mock_github.create_files.return_value = {"files_created": expected_create_files_count}

    # 2. Execution (Happy Path / Edge Case)
    workflow._generate_scaffold(username, idea_data, verbose)

    # 3. Validation

    # Verify Gemini called
    mock_gemini.generate_project_scaffold.assert_called_once_with(idea_data)

    # Verify README generated and created
    mock_build_readme.assert_called_once()
    mock_github.create_file.assert_called_once()

    create_file_kwargs = mock_github.create_file.call_args[1]
    assert create_file_kwargs['owner'] == username
    assert create_file_kwargs['repo'] == idea_data['slug']
    assert create_file_kwargs['path'] == "README.md"
    assert create_file_kwargs['content'] == "# README"

    # Verify Scaffold files created
    if expected_create_files_count > 0:
        mock_github.create_files.assert_called_once()
        create_files_kwargs = mock_github.create_files.call_args[1]
        assert create_files_kwargs['owner'] == username
        assert create_files_kwargs['repo'] == idea_data['slug']
        assert len(create_files_kwargs['files']) == expected_create_files_count

        # Verify content logic (e.g. requirements.txt added if present)
        file_paths = [f['path'] for f in create_files_kwargs['files']]
        if scaffold_response.get('requirements'):
             assert "requirements.txt" in file_paths

        # Verify README filtered out from create_files
        assert "README.md" not in file_paths and "readme.md" not in file_paths

    else:
        mock_github.create_files.assert_not_called()
