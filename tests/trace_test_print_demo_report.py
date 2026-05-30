from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report

# Mental Model:
# Input: idea_data: dict[str, Any], scaffold: dict[str, Any], feature_maps: dict[str, Any] | None
# External Side Effects: Prints to stdout (using builtins.print and src.utils.reporter.print_panel).
# Output: None (returns implicitly) or raises AttributeError on invalid data (e.g. scaffold=None)


@pytest.fixture
def mock_idea_data() -> dict[str, Any]:
    return {"title": "Test App", "slug": "test-app"}


@pytest.fixture
def happy_scaffold() -> dict[str, Any]:
    return {
        "files": [{"path": "main.py", "description": "Main file"}],
        "requirements": ["pytest"],
        "run_command": "python main.py",
    }


@pytest.fixture
def happy_feature_maps() -> dict[str, Any]:
    return {
        "mvp_features": [{"name": "Feature 1", "priority": "High"}],
        "production_features": [{"name": "Feature 2", "priority": "Medium"}],
    }


@pytest.mark.parametrize(
    "scaffold_type, feature_maps_type, expected",
    [
        ("happy", "happy", None),  # Happy Path
        ("empty", "empty", None),  # Edge Case
        ("none", "none", AttributeError),  # Error State
    ],
)
def test_print_demo_report_behavior(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    mock_idea_data: dict[str, Any],
    scaffold_type: str,
    feature_maps_type: str,
    expected: type[Exception] | None,
) -> None:
    # Resolve parameters to avoid lazy_fixture issues
    scaffold: dict[str, Any] | None = None
    if scaffold_type == "happy":
        scaffold = request.getfixturevalue("happy_scaffold")
    elif scaffold_type == "empty":
        scaffold = {}

    feature_maps: dict[str, Any] | None = None
    if feature_maps_type == "happy":
        feature_maps = request.getfixturevalue("happy_feature_maps")
    elif feature_maps_type == "empty":
        feature_maps = None

    # 1. Setup Mocks (Namespace Verified)
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_idea_data, scaffold, feature_maps)  # type: ignore[arg-type]
    else:
        print_demo_report(mock_idea_data, scaffold, feature_maps)  # type: ignore[arg-type]
        mock_print_panel.assert_called()
        mock_print.assert_called()
