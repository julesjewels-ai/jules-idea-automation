from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def happy_path_data() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    idea_data = {"title": "Test Idea"}
    scaffold = {
        "files": [{"path": "main.py", "description": "Main entry point"}],
        "requirements": ["pytest", "requests"],
        "run_command": "python main.py",
    }
    feature_maps = {
        "mvp_features": [
            {"name": "Auth", "priority": "P0"},
            {"name": "DB", "priority": "P1"},
            {"name": "API", "priority": "P1"},
            {"name": "UI", "priority": "P2"},
            {"name": "Logging", "priority": "P2"},
            {"name": "Extra MVP", "priority": "P3"},
        ],
        "production_features": [
            {"name": "Scale", "priority": "P1"},
            {"name": "Monitor", "priority": "P2"},
            {"name": "Alerts", "priority": "P2"},
            {"name": "Extra Prod", "priority": "P3"},
        ],
    }
    return idea_data, scaffold, feature_maps


@pytest.fixture
def edge_case_data() -> tuple[dict[str, Any], dict[str, Any], None]:
    idea_data: dict[str, Any] = {}
    scaffold: dict[str, Any] = {"files": [], "requirements": [], "run_command": ""}
    return idea_data, scaffold, None


@pytest.fixture
def error_state_data() -> tuple[dict[str, Any], Any, None]:
    return {}, None, None


@pytest.mark.parametrize(
    "data_fixture, expected",
    [
        ("happy_path_data", None),  # Happy Path
        ("edge_case_data", None),  # Edge Case
        ("error_state_data", AttributeError),  # Error State
    ],
)
def test_print_demo_report_behavior(
    request: pytest.FixtureRequest, mocker: MockerFixture, data_fixture: str, expected: Any
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The module uses builtins.print and src.utils.reporter.print_panel
    mock_print = mocker.patch("builtins.print")
    # Because print_panel is in the same module, we mock it via the module's namespace
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel")

    # Extract data from fixture
    idea_data, scaffold, feature_maps = request.getfixturevalue(data_fixture)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        # Call the target function
        print_demo_report(idea_data, scaffold, feature_maps)

        # Verify return value
        assert expected is None

        # Verify side effects
        mock_print.assert_called()
        mock_print_panel.assert_called()
