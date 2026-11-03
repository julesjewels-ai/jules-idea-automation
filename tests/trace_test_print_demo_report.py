import pytest
from pytest_mock import MockerFixture
from typing import Any
from src.utils.reporter import print_demo_report

@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "idea_data": {"title": "Test Idea"},
        "scaffold": {
            "files": [
                {"path": "src/main.py", "description": "Main entry point"},
                {"path": "README.md", "description": "Documentation"}
            ],
            "requirements": ["pytest", "pydantic"],
            "run_command": "python src/main.py"
        },
        "feature_maps": {
            "mvp_features": [
                {"name": "Feature 1", "priority": "High"},
                {"name": "Feature 2", "priority": "Medium"}
            ],
            "production_features": [
                {"name": "Prod Feature 1", "priority": "Low"}
            ]
        }
    }

@pytest.mark.parametrize("idea_data_override, scaffold_override, feature_maps_override, expected", [
    (None, None, None, None),  # Happy Path (uses mock_context defaults)
    ({}, {}, {}, None),        # Edge Case (empty dictionaries, no files, no requirements, no feature_maps items)
    (None, None, ValueError, AttributeError), # Error State (invalid type for feature_maps causing error during .get())
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    idea_data_override: Any,
    scaffold_override: Any,
    feature_maps_override: Any,
    expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print")

    idea_data = idea_data_override if idea_data_override is not None else mock_context["idea_data"]
    scaffold = scaffold_override if scaffold_override is not None else mock_context["scaffold"]
    feature_maps = feature_maps_override if feature_maps_override is not None else mock_context["feature_maps"]

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        result = print_demo_report(idea_data, scaffold, feature_maps)
        assert result is expected

        # Verify print_panel was called (at least once for What's Next, plus scaffold, plus feature maps if provided)
        assert mock_print_panel.call_count >= 2
        # Verify print was called
        assert mock_print.call_count >= 1
