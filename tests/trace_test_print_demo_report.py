from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "idea_data": {"title": "Test Idea", "description": "A great idea"},
        "scaffold": {
            "files": [
                {"path": "src/main.py", "description": "Main entry point"},
                {"path": "README.md", "description": "Documentation"},
            ],
            "requirements": ["requests", "pytest"],
            "run_command": "python src/main.py",
        },
        "feature_maps": {
            "mvp_features": [
                {"name": "Auth", "priority": "High"},
                {"name": "DB", "priority": "High"},
            ],
            "production_features": [
                {"name": "Scaling", "priority": "Low"},
            ],
        },
    }


@pytest.mark.parametrize(
    "scenario, expected",
    [
        ("happy_path", "success"),
        ("edge_case", "success"),
        ("error_state", AttributeError),
    ],
)
def test_print_demo_report_behavior(
    mocker: MockerFixture, mock_context: dict[str, Any], scenario: str, expected: str | type[Exception]
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The target function `print_demo_report` is in `src.utils.reporter`.
    # It calls `print_panel` locally and the built-in `print`.
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # Prepare input based on scenario
    idea_data = mock_context["idea_data"]

    if scenario == "happy_path":
        scaffold = mock_context["scaffold"]
        feature_maps = mock_context["feature_maps"]
    elif scenario == "edge_case":
        scaffold = {}
        feature_maps = None
    elif scenario == "error_state":
        scaffold = "invalid_scaffold_type"  # Should be dict, string will raise AttributeError on .get()
        feature_maps = None

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        print_demo_report(idea_data, scaffold, feature_maps)

        # Verify side effects
        if scenario == "happy_path":
            # print_panel should be called at least twice (scaffold, feature maps, next steps)
            assert mock_print_panel.call_count == 3
            mock_print.assert_called()
        elif scenario == "edge_case":
            # Feature maps are skipped, so print_panel is called twice (scaffold, next steps)
            assert mock_print_panel.call_count == 2
            mock_print.assert_called()
