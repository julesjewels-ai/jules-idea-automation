from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_scaffold() -> dict[str, Any]:
    return {
        "files": [{"path": "main.py", "description": "Entry point"}],
        "requirements": ["pytest"],
        "run_command": "pytest",
    }


@pytest.fixture
def mock_feature_maps() -> dict[str, Any]:
    return {
        "mvp_features": [{"name": "Auth", "priority": "High"}],
        "production_features": [{"name": "Rate Limiting", "priority": "Medium"}],
    }


@pytest.fixture
def empty_dict() -> dict[str, Any]:
    return {}


@pytest.mark.parametrize(
    "idea_data_key, scaffold_key, feature_maps_key, expected_type",
    [
        ("empty_dict", "mock_scaffold", "mock_feature_maps", type(None)),  # Happy Path
        ("empty_dict", "empty_dict", None, type(None)),  # Edge Case
        ("empty_dict", None, "empty_dict", AttributeError),  # Error State
    ],
)
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
    idea_data_key: str,
    scaffold_key: str | None,
    feature_maps_key: str | None,
    expected_type: type[Exception] | type[None],
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print = mocker.patch("builtins.print")
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel")

    idea_data = request.getfixturevalue(idea_data_key)
    scaffold = request.getfixturevalue(scaffold_key) if scaffold_key else None
    feature_maps = request.getfixturevalue(feature_maps_key) if feature_maps_key else None

    # 2. Execution & Validation
    if isinstance(expected_type, type) and issubclass(expected_type, Exception):
        with pytest.raises(expected_type):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        print_demo_report(idea_data, scaffold, feature_maps)

        if scaffold_key == "mock_scaffold" and feature_maps_key == "mock_feature_maps":
            assert mock_print_panel.call_count == 3
            assert mock_print.call_count == 3
        elif scaffold_key == "empty_dict" and feature_maps_key is None:
            assert mock_print_panel.call_count == 2
            assert mock_print.call_count == 2
