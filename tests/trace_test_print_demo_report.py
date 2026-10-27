import builtins
import pytest
from typing import Any
from pytest_mock import MockerFixture
from src.utils.reporter import print_demo_report

@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "idea_data": {
            "title": "Test Demo App",
            "description": "A demo application",
        },
        "scaffold": {
            "files": [{"path": "main.py", "description": "Entry point"}, "README.md"],
            "requirements": ["pytest", "requests"],
            "run_command": "python main.py"
        },
        "feature_maps": {
            "mvp_features": [{"name": "Core Feature", "priority": "High"}],
            "production_features": [{"name": "Auth", "priority": "Medium"}]
        }
    }

@pytest.mark.parametrize("scenario, updates, expected", [
    # Happy Path: All data is present
    ("happy_path", {}, None),

    # Edge Case: Missing optional parts (e.g. no feature maps, no reqs/run_cmd)
    ("edge_case", {
        "feature_maps": None,
        "scaffold": {"files": []}
    }, None),

    # Error State: Bad type for scaffold causing AttributeError when .get is called
    ("error_state", {
        "scaffold": None
    }, AttributeError),
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    scenario: str,
    updates: dict[str, Any],
    expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The file uses `print_panel(...)` (imported internally) and `print(...)` (built-in)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print")

    # Apply updates for the current scenario
    for key, val in updates.items():
        mock_context[key] = val

    idea_data = mock_context["idea_data"]
    scaffold = mock_context["scaffold"]
    feature_maps = mock_context["feature_maps"]

    # 2. Execution & Validation
    if expected is not None and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        print_demo_report(idea_data, scaffold, feature_maps)

        # Verify Side Effects
        assert mock_print_panel.call_count >= 1

        if scenario == "happy_path":
            # Scaffold panel, feature map panel, next steps panel
            assert mock_print_panel.call_count == 3
            # Asserts some calls to print
            assert mock_print.call_count >= 2
        elif scenario == "edge_case":
            # Scaffold panel (empty) and next steps panel
            assert mock_print_panel.call_count == 2
