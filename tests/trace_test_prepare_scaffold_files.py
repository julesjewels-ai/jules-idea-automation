import pytest
from pytest_mock import MockerFixture
from typing import Any

from src.core.workflow import IdeaWorkflow


@pytest.fixture
def workflow_instance(mocker: MockerFixture) -> IdeaWorkflow:
    """Provides a fresh IdeaWorkflow instance with an isolated namespace."""
    mock_github = mocker.MagicMock()
    mock_gemini = mocker.MagicMock()
    mock_jules = mocker.MagicMock()
    mock_event_bus = mocker.MagicMock()
    return IdeaWorkflow(
        github=mock_github,
        gemini=mock_gemini,
        jules=mock_jules,
        event_bus=mock_event_bus
    )


@pytest.mark.parametrize(
    "scaffold, expected_files, expected_warning",
    [
        # Happy Path: Standard list of files and string requirements
        (
            {
                "files": [
                    {"path": "main.py", "content": "print('hello')"},
                    {"path": "utils.py", "content": "def add(): pass"}
                ],
                "requirements": ["pytest", "requests"]
            },
            [
                {"path": "main.py", "content": "print('hello')"},
                {"path": "utils.py", "content": "def add(): pass"},
                {"path": "requirements.txt", "content": "pytest\nrequests"}
            ],
            False,
        ),
        # Happy Path 2: Missing requirements
        (
            {
                "files": [
                    {"path": "main.py", "content": "print('hello')"}
                ]
            },
            [
                {"path": "main.py", "content": "print('hello')"}
            ],
            False,
        ),
        # Edge Case 1: 'files' is not a list (e.g. dict)
        (
            {
                "files": {"path": "main.py", "content": "print('hello')"},
                "requirements": ["pytest"]
            },
            [],
            True,
        ),
        # Edge Case 2: 'files' is missing
        (
            {
                "requirements": ["pytest"]
            },
            [],
            False,
        ),
        # Edge Case 3: 'requirements' is a dict
        (
            {
                "files": [{"path": "main.py", "content": "print('hello')"}],
                "requirements": {"pytest": ">=7", "requests": "*", "black": "latest", "mypy": ""}
            },
            [
                {"path": "main.py", "content": "print('hello')"},
                {"path": "requirements.txt", "content": "pytest>=7\nrequests\nblack\nmypy"}
            ],
            False,
        ),
        # Edge Case 4: 'requirements' is a list of dicts
        (
            {
                "files": [{"path": "main.py", "content": "print('hello')"}],
                "requirements": [
                    {"package": "pytest", "version": ">=7"},
                    {"name": "requests"},
                    {"package": "black", "constraint": "==22.3.0"}
                ]
            },
            [
                {"path": "main.py", "content": "print('hello')"},
                {"path": "requirements.txt", "content": "pytest>=7\nrequests\nblack==22.3.0"}
            ],
            False,
        ),
        # Edge Case 5: 'requirements' is a single string or unusual type
        (
            {
                "files": [{"path": "main.py", "content": "print('hello')"}],
                "requirements": "pytest>=7"
            },
            [
                {"path": "main.py", "content": "print('hello')"},
                {"path": "requirements.txt", "content": "pytest>=7"}
            ],
            False,
        ),
        # Error State / Malformed: Mixed requirements and invalid files
        (
            {
                "files": [
                    {"wrong": "format"},
                    "not a dict",
                    {"path": "README.md", "content": "should be skipped"},
                    {"path": "test.py"} # valid but no content
                ],
                "requirements": [123, {"foo": "bar"}]
            },
            [
                {"path": "test.py", "content": ""},
                {"path": "requirements.txt", "content": "123"}
            ],
            False,
        )
    ]
)
def test_prepare_scaffold_files_behavior(
    mocker: MockerFixture,
    workflow_instance: IdeaWorkflow,
    scaffold: dict[str, Any],
    expected_files: list[dict[str, str]],
    expected_warning: bool
) -> None:
    """Test _prepare_scaffold_files handling of various scaffold structures."""

    # 1. Setup Mocks (Namespace Verified)
    # The module uses: logger = logging.getLogger(__name__)
    mock_logger = mocker.patch("src.core.workflow.logger", autospec=True)

    # 2. Execution & Validation
    result = workflow_instance._prepare_scaffold_files(scaffold)

    # Verify return value
    assert result == expected_files

    # Verify side effects
    if expected_warning:
        mock_logger.warning.assert_called_once()
        # Verify the warning message contains expected text
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "is not a list" in warning_msg
    else:
        # We don't expect the warning about files not being a list
        # Though `_process_file_entry` might log its own warnings for malformed entries
        # Let's ensure the specific warning for files_list type is handled properly.
        # It's cleaner to check that our target warning wasn't called.
        # If it was called, check it wasn't the "files not a list" one unless expected
        for call in mock_logger.warning.call_args_list:
            assert "is not a list" not in call[0][0]
