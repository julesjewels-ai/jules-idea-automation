import pytest
from typing import Any
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report

@pytest.fixture
def mock_idea_data() -> dict[str, Any]:
    return {"title": "Test App"}

@pytest.fixture
def happy_scaffold() -> dict[str, Any]:
    return {
        "files": [{"path": "main.py", "description": "Entry point"}],
        "requirements": ["pytest"],
        "run_command": "python main.py",
    }

@pytest.fixture
def happy_feature_maps() -> dict[str, Any]:
    return {
        "mvp_features": [{"name": "Feature 1", "priority": "P0"}],
        "production_features": [{"name": "Feature 2", "priority": "P1"}],
    }

@pytest.fixture
def empty_dict() -> dict[str, Any]:
    return {}

@pytest.fixture
def none_val() -> None:
    return None

@pytest.mark.parametrize("scaffold_name, feature_maps_name, expected", [
    ("happy_scaffold", "happy_feature_maps", None),   # Happy Path
    ("empty_dict", "none_val", None),                 # Edge Case
    ("none_val", "none_val", AttributeError),         # Error State
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
    mock_idea_data: dict[str, Any],
    scaffold_name: str,
    feature_maps_name: str,
    expected: type[Exception] | None,
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    mock_print = mocker.patch("builtins.print", autospec=True)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)

    scaffold: dict[str, Any] | None = request.getfixturevalue(scaffold_name)
    feature_maps: dict[str, Any] | None = request.getfixturevalue(feature_maps_name)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_idea_data, scaffold, feature_maps)  # type: ignore[arg-type]
    else:
        # For Happy Path / Edge Case, we know scaffold is not None
        result = print_demo_report(mock_idea_data, scaffold, feature_maps)  # type: ignore[arg-type]
        assert result == expected

        # Verify side effects
        if feature_maps_name == "happy_feature_maps":
            assert mock_print_panel.call_count == 3
            assert mock_print.call_count == 3
        else:
            assert mock_print_panel.call_count == 2
            assert mock_print.call_count == 2
