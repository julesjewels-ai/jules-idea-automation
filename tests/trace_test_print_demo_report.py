from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def base_idea_data() -> dict[str, Any]:
    return {"title": "My Awesome Idea"}


@pytest.fixture
def base_scaffold() -> dict[str, Any]:
    return {
        "files": [
            {"path": "main.py", "description": "Entry point"},
            {"path": "requirements.txt", "description": "Dependencies"},
        ],
        "requirements": ["pytest", "requests"],
        "run_command": "python main.py",
    }


@pytest.fixture
def base_feature_maps() -> dict[str, Any]:
    return {
        "mvp_features": [{"name": "Auth", "priority": "P0"}, {"name": "DB", "priority": "P0"}],
        "production_features": [{"name": "Monitoring", "priority": "P2"}],
    }


@pytest.mark.parametrize(
    "use_scaffold, use_feature_maps, expected_panel_calls, expected_exception",
    [
        (True, True, 3, None),  # Happy Path
        (True, False, 2, None),  # Edge Case
        (False, False, 0, AttributeError),  # Error State
    ],
)
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    base_idea_data: dict[str, Any],
    base_scaffold: dict[str, Any],
    base_feature_maps: dict[str, Any],
    use_scaffold: bool,
    use_feature_maps: bool,
    expected_panel_calls: int,
    expected_exception: type[Exception] | None,
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    scaffold_val = base_scaffold if use_scaffold else None
    feature_maps_val = base_feature_maps if use_feature_maps else None

    # 2. Execution & Validation
    if expected_exception:
        with pytest.raises(expected_exception):
            print_demo_report(base_idea_data, scaffold_val, feature_maps_val)  # type: ignore[arg-type]
    else:
        result = print_demo_report(base_idea_data, scaffold_val, feature_maps_val)  # type: ignore[arg-type]

        assert result is None
        assert mock_print_panel.call_count == expected_panel_calls
        assert mock_print.call_count == expected_panel_calls
