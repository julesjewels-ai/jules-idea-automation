import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict:
    return {
        "idea_data": {"title": "Test Title"},
    }


@pytest.fixture
def mock_scaffold_happy() -> dict:
    return {
        "files": [{"path": "main.py", "description": "Entry"}],
        "requirements": ["requests"],
        "run_command": "python main.py",
    }


@pytest.fixture
def mock_feature_maps_happy() -> dict:
    return {
        "mvp_features": [{"name": "Auth", "priority": "P0"}],
        "production_features": [{"name": "Scale", "priority": "P1"}],
    }


@pytest.mark.parametrize(
    "scaffold_fixture, feature_maps_fixture, expected",
    [
        ("mock_scaffold_happy", "mock_feature_maps_happy", None),  # Happy Path
        ("empty_dict", "none_val", None),  # Edge Case
        ("corrupt_val", "empty_dict", AttributeError),  # Error State
    ],
)
def test_target_function_behavior(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    mock_context: dict,
    scaffold_fixture: str,
    feature_maps_fixture: str,
    expected: type[Exception] | None,
) -> None:
    # Resolve fixtures by name
    scaffold = (
        request.getfixturevalue(scaffold_fixture)
        if scaffold_fixture not in ("empty_dict", "corrupt_val")
        else ({} if scaffold_fixture == "empty_dict" else "corrupt_data")
    )
    feature_maps = (
        request.getfixturevalue(feature_maps_fixture)
        if feature_maps_fixture not in ("empty_dict", "none_val")
        else ({} if feature_maps_fixture == "empty_dict" else None)
    )

    # 1. Setup Mocks (Namespace Verified)
    # FIXME: Verify patch path.
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print")

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(mock_context["idea_data"], scaffold, feature_maps)  # type: ignore
    else:
        result = print_demo_report(mock_context["idea_data"], scaffold, feature_maps)  # type: ignore
        assert result == expected
        mock_print_panel.assert_called()
        mock_print.assert_called()
