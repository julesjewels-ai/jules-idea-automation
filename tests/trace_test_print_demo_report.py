from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


class MockFile:
    def __init__(self, path: str, description: str) -> None:
        self.path = path
        self.description = description


class MockFeature:
    def __init__(self, name: str, priority: str) -> None:
        self.name = name
        self.priority = priority


HAPPY_SCAFFOLD: dict[str, Any] = {
    "files": [MockFile("main.py", "Main entry point"), {"path": "utils.py", "description": "Utilities"}],
    "requirements": ["pytest", "pydantic"],
    "run_command": "pytest tests/",
}

HAPPY_FEATURE_MAPS: dict[str, Any] = {
    "mvp_features": [
        MockFeature("Auth", "High"),
        MockFeature("DB", "High"),
        {"name": "API", "priority": "Medium"},
        {"name": "UI", "priority": "Medium"},
        {"name": "Docs", "priority": "Low"},
        {"name": "Tests", "priority": "Low"},
    ],
    "production_features": [
        MockFeature("Scale", "High"),
        MockFeature("Cache", "Medium"),
        {"name": "Metrics", "priority": "Low"},
        {"name": "Alerts", "priority": "Low"},
    ],
}


@pytest.fixture
def mock_idea_data() -> dict[str, Any]:
    return {"title": "Test Idea", "description": "Test Description"}


@pytest.mark.parametrize(
    "scaffold, feature_maps, expected",
    [
        (HAPPY_SCAFFOLD, HAPPY_FEATURE_MAPS, None),  # Happy Path
        ({}, {}, None),  # Edge Case
        (None, None, AttributeError),  # Error State
    ],
)
def test_print_demo_report_behavior(
    mocker: MockerFixture, mock_idea_data: dict[str, Any], scaffold: Any, feature_maps: Any, expected: Any
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_idea_data, scaffold, feature_maps)
    else:
        result = print_demo_report(mock_idea_data, scaffold, feature_maps)
        assert result == expected
        assert mock_print_panel.call_count >= 2
        assert mock_print.call_count >= 2
