import pytest
from pytest_mock import MockerFixture
from typing import Any

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict[str, dict[str, Any] | None]:
    return {
        "idea_data": {"title": "Test App", "description": "A test app", "slug": "test-app"},
        "scaffold": {
            "files": [
                {"path": "main.py", "description": "Main entry point"}
            ],
            "requirements": ["pytest", "requests"],
            "run_command": "python main.py"
        },
        "feature_maps": {
            "mvp_features": [{"name": "Auth", "priority": "High"}],
            "production_features": [{"name": "Scaling", "priority": "Low"}]
        }
    }


@pytest.mark.parametrize("scenario, modify_context, expected_error", [
    ("happy_path", {}, None),
    ("edge_case_empty", {"scaffold": {}, "feature_maps": None}, None),
    ("error_state_invalid_type", {"scaffold": None}, AttributeError),
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, dict[str, Any] | None],
    scenario: str,
    modify_context: dict[str, Any],
    expected_error: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The function prints using standard print and internal print_panel.
    mock_print = mocker.patch("builtins.print", autospec=True)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)

    # Prepare context
    for key, value in modify_context.items():
        mock_context[key] = value

    idea_data = mock_context["idea_data"]
    scaffold = mock_context["scaffold"]
    feature_maps = mock_context["feature_maps"]

    assert idea_data is not None

    # 2. Execution & Validation
    if expected_error is not None:
        with pytest.raises(expected_error):
            # type ignore to simulate invalid runtime data for error state
            print_demo_report(idea_data, scaffold, feature_maps)  # type: ignore[arg-type]
    else:
        print_demo_report(idea_data, scaffold, feature_maps)  # type: ignore[arg-type]

        # Verify side effects
        if scenario == "happy_path":
            # 3 panels: Scaffold Preview, Feature Maps, What's Next
            assert mock_print_panel.call_count == 3
            # Some regular print statements for spacing
            assert mock_print.call_count > 0
        elif scenario == "edge_case_empty":
            # 2 panels: Scaffold Preview, What's Next (no feature maps)
            assert mock_print_panel.call_count == 2
