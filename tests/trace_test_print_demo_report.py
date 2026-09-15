import pytest
from typing import Any
from pytest_mock import MockerFixture
from src.utils.reporter import print_demo_report

@pytest.fixture
def mock_scaffold() -> dict[str, Any]:
    return {
        "files": [{"path": "main.py", "description": "Main file"}],
        "requirements": ["pytest", "requests"],
        "run_command": "python main.py"
    }

@pytest.fixture
def mock_feature_maps() -> dict[str, Any]:
    return {
        "mvp_features": [{"name": "Auth", "priority": "P0"}],
        "production_features": [{"name": "Scaling", "priority": "P2"}]
    }

@pytest.mark.parametrize("scaffold_data, feature_maps_data, expected", [
    ("mock_scaffold", "mock_feature_maps", None),  # Happy Path
    ({}, None, None),                              # Edge Case (empty)
    ("invalid_type", None, AttributeError),        # Error State
])
def test_print_demo_report_behavior(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    scaffold_data: str | dict[str, Any],
    feature_maps_data: str | dict[str, Any] | None,
    expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print")

    # Resolve string fixture names to actual objects if needed
    scaffold = request.getfixturevalue(scaffold_data) if isinstance(scaffold_data, str) and scaffold_data.startswith("mock_") else scaffold_data
    feature_maps = request.getfixturevalue(feature_maps_data) if isinstance(feature_maps_data, str) and feature_maps_data.startswith("mock_") else feature_maps_data

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report({}, scaffold, feature_maps)
    else:
        result = print_demo_report({}, scaffold, feature_maps)
        assert result == expected
        mock_print_panel.assert_called()
