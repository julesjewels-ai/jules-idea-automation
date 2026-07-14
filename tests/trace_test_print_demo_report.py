import pytest
from pytest_mock import MockerFixture
from typing import Any
from src.utils.reporter import print_demo_report

@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "idea_data": {"title": "Test Idea"},
    }

@pytest.mark.parametrize("scaffold, feature_maps, expected", [
    (
        {"files": [{"path": "main.py", "description": "Main"}], "requirements": [], "run_command": "test"},
        {"mvp_features": [{"name": "Auth", "priority": "High"}], "production_features": [{"name": "Scale", "priority": "Medium"}]},
        None
    ), # Happy Path
    (
        {},
        None,
        None
    ), # Edge Case (empty/None)
    (
        None,
        None,
        AttributeError
    ), # Error State (triggering AttributeError on .get)
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    scaffold: dict[str, Any] | None,
    feature_maps: dict[str, Any] | None,
    expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # Target function uses print_panel from the same module and builtins.print.
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_context["idea_data"], scaffold, feature_maps) # type: ignore
    else:
        result = print_demo_report(
            mock_context["idea_data"],
            scaffold, # type: ignore
            feature_maps
        )
        assert result == expected
        mock_print_panel.assert_called()
        mock_print.assert_called()
