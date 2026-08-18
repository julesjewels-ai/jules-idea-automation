import pytest
from pytest_mock import MockerFixture
from typing import Any

from src.utils.reporter import print_demo_report

HAPPY_SCAFFOLD: dict[str, Any] = {
    "files": [{"path": "main.py", "description": "Entry point"}],
    "requirements": ["pytest"],
    "run_command": "pytest"
}
HAPPY_FEATURE_MAPS: dict[str, Any] = {
    "mvp_features": [{"name": "Auth", "priority": "P0"}],
    "production_features": [{"name": "Scaling", "priority": "P2"}]
}

@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {"idea_data": {"title": "Test Idea"}}

@pytest.mark.parametrize("scaffold, feature_maps, expected", [
    (HAPPY_SCAFFOLD, HAPPY_FEATURE_MAPS, None),        # Happy Path
    ({}, {}, None),                                    # Edge Case
    (None, None, AttributeError),                      # Error State
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    scaffold: dict[str, Any] | None,
    feature_maps: dict[str, Any] | None,
    expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # 2. Execution & Validation
    if expected is not None and isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_context["idea_data"], scaffold, feature_maps) # type: ignore
    else:
        result = print_demo_report(mock_context["idea_data"], scaffold, feature_maps) # type: ignore
        assert result == expected
        mock_print_panel.assert_called()
        mock_print.assert_called()
