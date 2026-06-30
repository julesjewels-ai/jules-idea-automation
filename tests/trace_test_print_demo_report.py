from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "idea_data": {"title": "Test Idea"},
        "scaffold": {
            "files": [{"path": "main.py", "description": "Entry point"}],
            "requirements": ["pytest"],
            "run_command": "python main.py",
        },
        "feature_maps": {
            "mvp_features": [{"name": "Auth", "priority": "P0"}],
            "production_features": [{"name": "Scaling", "priority": "P1"}],
        },
    }


@pytest.mark.parametrize(
    "scenario, expected",
    [
        ("happy_path", None),
        ("edge_case", None),
        ("error_state", AttributeError),
    ],
)
def test_print_demo_report_behavior(
    mocker: MockerFixture, mock_context: dict[str, Any], scenario: str, expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The file uses `print_panel(...)` (internal to reporter) and `print(...)` (builtins)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # 2. Setup scenario data
    if scenario == "edge_case":
        # Empty dicts for edge case
        kwargs = {"idea_data": {}, "scaffold": {}, "feature_maps": {}}
    elif scenario == "error_state":
        # None for scaffold will cause AttributeError: 'NoneType' object has no attribute 'get'
        kwargs = {
            "idea_data": {},
            "scaffold": None,  # type: ignore
            "feature_maps": None,
        }
    else:
        # Happy path
        kwargs = mock_context

    # 3. Execution & Validation
    if expected and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(**kwargs)
    else:
        print_demo_report(**kwargs)
        # Side effects validation
        assert mock_print_panel.called
        assert mock_print.called
