import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from src.core.workflow import IdeaWorkflow

@pytest.fixture
def mock_github():
    return MagicMock()

@pytest.fixture
def mock_gemini():
    return MagicMock()

@pytest.fixture
def mock_jules():
    return MagicMock()

@pytest.fixture
def idea_data():
    return {
        "title": "My Idea",
        "description": "A great idea",
        "slug": "my-idea",
        "tech_stack": ["Python"],
        "features": ["Feature 1"]
    }

@pytest.mark.parametrize("scaffold_result, expected_readme_called, expected_files_called, error_expected", [
    # Happy Path
    (
        {
            "requirements": ["requests"],
            "run_command": "python main.py",
            "files": [
                {"path": "main.py", "content": "print('hello')"},
                {"path": "README.md", "content": "ignored"}
            ]
        },
        True,
        True,
        None
    ),
    # Edge Case: Empty scaffold (no files, no requirements)
    (
        {
            "requirements": [],
            "run_command": "",
            "files": []
        },
        True,
        False,
        None
    ),
    # Error State: Gemini fails
    (
        RuntimeError("Gemini failed"),
        False,
        False,
        RuntimeError
    )
])
def test_generate_scaffold(
    mocker: MockerFixture,
    mock_github: MagicMock,
    mock_gemini: MagicMock,
    mock_jules: MagicMock,
    idea_data: dict,
    scaffold_result: dict | Exception,
    expected_readme_called: bool,
    expected_files_called: bool,
    error_expected: type[Exception] | None
):
    # 1. Setup Mocks (Namespace Verified)
    # We patch build_readme because it is imported in src.core.workflow
    mock_build_readme = mocker.patch("src.core.workflow.build_readme", return_value="# README Content")

    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

    if isinstance(scaffold_result, Exception):
        mock_gemini.generate_project_scaffold.side_effect = scaffold_result
    else:
        mock_gemini.generate_project_scaffold.return_value = scaffold_result
        # Mock create_files return value to match usage in verbose print
        mock_github.create_files.return_value = {"files_created": 2}

    # 2. Execution
    if error_expected:
        with pytest.raises(error_expected):
            workflow._generate_scaffold(username="testuser", idea_data=idea_data, verbose=True)
    else:
        workflow._generate_scaffold(username="testuser", idea_data=idea_data, verbose=True)

    # 3. Validation
    # Verify README creation
    if expected_readme_called:
        mock_build_readme.assert_called_once()
        mock_github.create_file.assert_called_once_with(
            owner="testuser",
            repo="my-idea",
            path="README.md",
            content="# README Content",
            message="Initial commit: Add README with project description"
        )
    else:
        # In error case, build_readme should not be reached
        mock_build_readme.assert_not_called()
        mock_github.create_file.assert_not_called()

    # Verify other files creation
    if expected_files_called:
        mock_github.create_files.assert_called_once()
        args, kwargs = mock_github.create_files.call_args

        # Verify kwargs
        assert kwargs['owner'] == "testuser"
        assert kwargs['repo'] == "my-idea"
        assert kwargs['message'] == "feat: Add MVP scaffold with SOLID structure"

        files_arg = kwargs['files']
        # Check that README.md is filtered out
        assert not any(f['path'].lower() == 'readme.md' for f in files_arg)

        # If requirements exist in scaffold, verify requirements.txt is added
        if isinstance(scaffold_result, dict) and scaffold_result.get('requirements'):
            assert any(f['path'] == 'requirements.txt' for f in files_arg)

    else:
        mock_github.create_files.assert_not_called()
