from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_idea_data() -> dict[str, Any]:
    return {"title": "Test Idea", "description": "A test description"}


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
        "mvp_features": [{"name": "Auth", "priority": "P0"}],
        "production_features": [{"name": "Monitoring", "priority": "P1"}],
    }


@pytest.fixture
def edge_scaffold() -> dict[str, Any]:
    return {"files": []}


@pytest.fixture
def error_scaffold() -> dict[str, Any]:
    return {"files": None}


@pytest.mark.parametrize(
    "scaffold_fixture_name, feature_maps_fixture_name, expected_exception",
    [
        ("happy_scaffold", "happy_feature_maps", None),
        ("edge_scaffold", None, None),
        ("error_scaffold", None, TypeError),
    ],
)
def test_target_function_behavior(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    mock_idea_data: dict[str, Any],
    scaffold_fixture_name: str,
    feature_maps_fixture_name: str | None,
    expected_exception: type[Exception] | None,
) -> None:
    # Resolve fixtures dynamically to avoid inline bloat
    scaffold_input = request.getfixturevalue(scaffold_fixture_name)
    feature_maps_input = request.getfixturevalue(feature_maps_fixture_name) if feature_maps_fixture_name else None

    # 1. Setup Mocks (Namespace Verified)
    mock_print = mocker.patch("builtins.print")
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)

    # 2. Execution & Validation
    if expected_exception:
        with pytest.raises(expected_exception):
            print_demo_report(mock_idea_data, scaffold_input, feature_maps_input)
    else:
        result = print_demo_report(mock_idea_data, scaffold_input, feature_maps_input)

        # Verify Return Value
        assert result is None

        # Verify Side Effects
        assert mock_print_panel.call_count > 0
        assert mock_print.call_count > 0
