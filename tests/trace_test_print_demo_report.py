from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


# Fixtures for complex objects
@pytest.fixture
def mock_idea_data() -> dict[str, Any]:
    return {"title": "Test Idea", "description": "A test description"}


@pytest.fixture
def mock_scaffold() -> dict[str, Any]:
    return {
        "files": [{"path": "main.py", "description": "Entry point"}],
        "requirements": ["pytest"],
        "run_command": "python main.py",
    }


@pytest.fixture
def mock_feature_maps() -> dict[str, Any]:
    return {
        "mvp_features": [{"name": "Auth", "priority": "P0"}],
        "production_features": [{"name": "Monitoring", "priority": "P1"}],
    }


# Data scenarios for Parametrization
# Happy Path
HAPPY_SCAFFOLD: dict[str, Any] = {
    "files": [{"path": "main.py", "description": "Entry point"}],
    "requirements": ["pytest"],
    "run_command": "python main.py",
}
HAPPY_FEATURE_MAPS: dict[str, Any] = {
    "mvp_features": [{"name": "Auth", "priority": "P0"}],
    "production_features": [{"name": "Monitoring", "priority": "P1"}],
}

# Edge Case (Missing Optional Data)
EDGE_SCAFFOLD: dict[str, Any] = {"files": []}
EDGE_FEATURE_MAPS: None = None

# Error State (Invalid Data Types that cause AttributeError)
# E.g., strings instead of lists for files, causing .get() or iteration to fail
ERROR_SCAFFOLD: dict[str, Any] = {"files": None}


@pytest.mark.parametrize(
    "scaffold_input, feature_maps_input, expected_exception",
    [
        (HAPPY_SCAFFOLD, HAPPY_FEATURE_MAPS, None),
        (EDGE_SCAFFOLD, EDGE_FEATURE_MAPS, None),
        (ERROR_SCAFFOLD, None, TypeError),
    ],
)
def test_target_function_behavior(
    mocker: MockerFixture,
    mock_idea_data: dict[str, Any],
    scaffold_input: dict[str, Any],
    feature_maps_input: dict[str, Any] | None,
    expected_exception: type[Exception] | None,
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The module uses built-in print and print_panel from within the module
    mock_print = mocker.patch("builtins.print")
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)

    # 2. Execution & Validation
    if expected_exception:
        with pytest.raises(expected_exception):
            print_demo_report(mock_idea_data, scaffold_input, feature_maps_input)
    else:
        print_demo_report(mock_idea_data, scaffold_input, feature_maps_input)

        # Verify Side Effects
        assert mock_print_panel.call_count > 0
        assert mock_print.call_count > 0
