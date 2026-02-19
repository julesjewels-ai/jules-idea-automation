import pytest
from pytest_mock import MockerFixture
from src.core.workflow import IdeaWorkflow

@pytest.fixture
def mock_context() -> dict:
    return {
        "title": "Test App",
        "description": "A test app",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["login"]
    }

@pytest.mark.parametrize("scaffold_data, expected_files_count, should_raise", [
    (
        # Happy Path
        {
            "requirements": ["pytest"],
            "run_command": "make run",
            "files": [
                {"path": "main.py", "content": "print('hello')"},
                {"path": "README.md", "content": "ignored"} # Should be ignored by _prepare_scaffold_files
            ]
        },
        2, # main.py + requirements.txt
        None
    ),
    (
        # Edge Case: No files, only requirements
        # NOTE: Current implementation of _prepare_scaffold_files returns early if 'files' is empty,
        # effectively ignoring 'requirements'. This test pins that behavior.
        {
            "requirements": ["pytest"],
            "run_command": "make run",
            "files": []
        },
        0, # requirements.txt is IGNORED due to early return
        None
    ),
    (
        # Error State
        Exception("Gemini Error"),
        0,
        Exception
    )
])
def test_generate_scaffold_behavior(
    mocker: MockerFixture,
    mock_context: dict,
    scaffold_data: dict | Exception,
    expected_files_count: int,
    should_raise: type[Exception] | None
) -> None:
    # 1. Setup Mocks
    mock_github = mocker.Mock()
    mock_gemini = mocker.Mock()
    mock_jules = mocker.Mock()

    # Patch build_readme as it is imported directly
    # The instructions say: "If the file uses from x import y, you MUST patch src.current_module.y."
    # src/core/workflow.py imports build_readme from src.core.readme_builder
    # So we patch src.core.workflow.build_readme
    mock_build_readme = mocker.patch("src.core.workflow.build_readme", return_value="# README")

    workflow = IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

    # 2. Execution & Validation
    if should_raise and isinstance(scaffold_data, Exception):
        mock_gemini.generate_project_scaffold.side_effect = scaffold_data
        with pytest.raises(type(scaffold_data)):
            workflow._generate_scaffold("testuser", mock_context, verbose=False)

        mock_gemini.generate_project_scaffold.assert_called_once_with(mock_context)
        # Should not proceed to build_readme or github calls if gemini fails
        mock_build_readme.assert_not_called()
        mock_github.create_file.assert_not_called()
        mock_github.create_files.assert_not_called()

    else:
        mock_gemini.generate_project_scaffold.return_value = scaffold_data
        # Mock create_files return value (it returns a dict)
        mock_github.create_files.return_value = {"files_created": expected_files_count}

        workflow._generate_scaffold("testuser", mock_context, verbose=False)

        # Verify interactions
        mock_gemini.generate_project_scaffold.assert_called_once_with(mock_context)
        mock_build_readme.assert_called_once()

        # Verify README creation (First commit)
        mock_github.create_file.assert_called_once()
        assert mock_github.create_file.call_args[1]['path'] == "README.md"
        assert mock_github.create_file.call_args[1]['content'] == "# README"
        assert mock_github.create_file.call_args[1]['owner'] == "testuser"
        assert mock_github.create_file.call_args[1]['repo'] == mock_context['slug']

        # Verify Scaffold creation (Second commit)
        if expected_files_count > 0:
            mock_github.create_files.assert_called_once()
            files_arg = mock_github.create_files.call_args[1]['files']
            assert len(files_arg) == expected_files_count
            assert mock_github.create_files.call_args[1]['owner'] == "testuser"
            assert mock_github.create_files.call_args[1]['repo'] == mock_context['slug']
        else:
            mock_github.create_files.assert_not_called()
