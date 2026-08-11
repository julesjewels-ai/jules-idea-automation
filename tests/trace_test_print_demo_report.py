from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_idea_data() -> dict[str, Any]:
    return {
        "title": "Test App",
        "description": "A test application.",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["feature-1"],
    }


@pytest.fixture
def mock_scaffold() -> dict[str, Any]:
    return {
        "files": [{"path": "main.py", "description": "Entry point"}],
        "requirements": ["pytest"],
        "run_command": "python main.py",
    }


@pytest.mark.parametrize(
    "feature_maps, expected_error",
    [
        (
            {
                "mvp_features": [{"name": "Auth", "priority": "high"}],
                "production_features": [{"name": "Scaling", "priority": "low"}],
            },
            None,
        ),  # Happy Path
        ({}, None),  # Edge Case: Missing feature maps
        (
            "invalid_feature_maps",
            AttributeError,
        ),  # Error State: Invalid type for feature_maps (not a dict, string has no 'get')
    ],
)
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_idea_data: dict[str, Any],
    mock_scaffold: dict[str, Any],
    feature_maps: Any,
    expected_error: type[Exception] | None,
) -> None:
    # 1. Setup Mocks (Namespace Verified: src.utils.reporter.print_panel)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)

    # 2. Execution & Validation
    if expected_error:
        with pytest.raises(expected_error):
            print_demo_report(mock_idea_data, mock_scaffold, feature_maps)
    else:
        print_demo_report(mock_idea_data, mock_scaffold, feature_maps)

        # Verify side effects:
        # print_demo_report calls print_panel at least 2 times (MVP Scaffold Preview and What's Next).
        # It may call it 3 times if feature_maps contains elements.
        assert mock_print_panel.call_count >= 2
