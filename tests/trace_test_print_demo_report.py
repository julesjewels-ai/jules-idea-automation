from typing import Any, Type, Union

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "idea_data": {"title": "Test Idea", "description": "A great idea"},
        "scaffold": {
            "files": [{"path": "main.py", "description": "Entry point"}],
            "requirements": ["pytest", "requests"],
            "run_command": "python main.py",
        },
        "feature_maps": {
            "mvp_features": [{"name": "Auth", "priority": "P0"}],
            "production_features": [{"name": "Billing", "priority": "P1"}],
        },
    }


@pytest.fixture
def edge_case_context() -> dict[str, Any]:
    return {"idea_data": {}, "scaffold": {}, "feature_maps": None}


@pytest.fixture
def error_case_context() -> dict[str, Any]:
    return {
        "idea_data": {},
        "scaffold": {"files": 42},  # Intentionally bad type to trigger TypeError
        "feature_maps": None,
    }


@pytest.mark.parametrize(
    "input_fixture_name, expected",
    [
        ("mock_context", 3),  # Happy Path: 3 print_panel calls
        ("edge_case_context", 2),  # Edge Case: 2 print_panel calls (No feature map)
        ("error_case_context", TypeError),  # Error State: TypeError because files is int
    ],
)
def test_print_demo_report_behavior(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    input_fixture_name: str,
    expected: Union[int, Type[Exception]],
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The file imports `print_panel` implicitly via being in the same module, but uses it directly.
    # It also uses built-in `print`. We patch them in the `src.utils.reporter` module.
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    input_data = request.getfixturevalue(input_fixture_name)
    idea_data = input_data["idea_data"]
    scaffold = input_data["scaffold"]
    feature_maps = input_data["feature_maps"]

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        result = print_demo_report(idea_data, scaffold, feature_maps)

        # Verify Return Value
        assert result is None

        # Verify Side Effects
        assert mock_print_panel.call_count == expected
        assert mock_print.call_count == expected
