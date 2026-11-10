import pytest
from pytest_mock import MockerFixture
from typing import Any

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "idea_data": {
            "title": "Test App",
        },
        "scaffold": {
            "files": [
                {"path": "main.py", "description": "Main entry point"}
            ],
            "requirements": ["pytest"],
            "run_command": "python main.py"
        },
        "feature_maps": {
            "mvp_features": [
                {"name": "Auth", "priority": "P0"}
            ],
            "production_features": [
                {"name": "Analytics", "priority": "P2"}
            ]
        }
    }


@pytest.mark.parametrize("input_val, expected", [
    ("valid_input", None),                 # Happy Path
    (None, AttributeError),                # Edge Case
    ("corrupt_data", AttributeError),      # Error State
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    input_val: Any,
    expected: Any
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The function prints to stdout via `print` and `print_panel`
    mock_print = mocker.patch("builtins.print", autospec=True)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_context["idea_data"], input_val, mock_context["feature_maps"]) # type: ignore
    else:
        # Expected success
        # Here input_val is "valid_input", so we use the mock context scaffold
        print_demo_report(
            mock_context["idea_data"],
            mock_context["scaffold"],
            mock_context["feature_maps"]
        )

        # Verify side effects
        # `print_panel` should be called multiple times (Scaffold Preview, Feature Maps, What's Next)
        assert mock_print_panel.call_count >= 3

        # `print` should be called to add spacing
        assert mock_print.call_count >= 3
