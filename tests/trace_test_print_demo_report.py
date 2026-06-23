from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {"title": "Test Idea", "description": "A test idea"}


@pytest.fixture
def mock_scaffold(request: pytest.FixtureRequest) -> Any:
    if request.param == "happy":
        return {
            "files": [{"path": "main.py", "description": "Main file"}],
            "requirements": ["pytest"],
            "run_command": "pytest",
        }
    elif request.param == "edge":
        return {}
    return None


@pytest.fixture
def mock_feature_maps(request: pytest.FixtureRequest) -> Any:
    if request.param == "happy":
        return {
            "mvp_features": [
                {"name": "Auth", "priority": "High"},
                {"name": "DB", "priority": "High"},
                {"name": "API", "priority": "High"},
                {"name": "UI", "priority": "Medium"},
                {"name": "Docs", "priority": "Low"},
                {"name": "Extra", "priority": "Low"},
            ],
            "production_features": [
                {"name": "Scaling", "priority": "High"},
                {"name": "Cache", "priority": "Medium"},
                {"name": "Metrics", "priority": "Low"},
                {"name": "Extra Prod", "priority": "Low"},
            ],
        }
    return None


@pytest.mark.parametrize(
    "mock_scaffold, mock_feature_maps, expected",
    [
        ("happy", "happy", None),  # Happy Path
        ("edge", "edge", None),  # Edge Case
        ("error", "error", AttributeError),  # Error State
    ],
    indirect=["mock_scaffold", "mock_feature_maps"],
)
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    mock_scaffold: dict[str, Any] | None,
    mock_feature_maps: dict[str, Any] | None,
    expected: type[Exception] | None,
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_context, mock_scaffold, mock_feature_maps)  # type: ignore
    else:
        result = print_demo_report(mock_context, mock_scaffold, mock_feature_maps)  # type: ignore
        assert result == expected
        mock_print_panel.assert_called()
        mock_print.assert_called()
