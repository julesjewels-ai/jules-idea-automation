import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_idea_data() -> dict[str, str]:
    return {"title": "Test App"}


@pytest.fixture
def mock_scaffold() -> dict[str, list[dict[str, str]] | list[str] | str]:
    return {
        "files": [{"path": "main.py", "description": "Main logic"}],
        "requirements": ["pytest", "requests"],
        "run_command": "python main.py",
    }


@pytest.fixture
def mock_scaffold_empty() -> dict[str, list[str]]:
    return {
        "files": [],
        "requirements": [],
    }


@pytest.fixture
def mock_feature_maps() -> dict[str, list[dict[str, str]]]:
    return {
        "mvp_features": [{"name": "Auth", "priority": "P0"}],
        "production_features": [{"name": "Cache", "priority": "P1"}],
    }


@pytest.mark.parametrize(
    "idea_fixture, scaffold_fixture, fm_fixture, expected",
    [
        # Happy Path
        ("mock_idea_data", "mock_scaffold", "mock_feature_maps", None),
        # Edge Case (Missing Optional Features)
        ("mock_idea_data", "mock_scaffold_empty", None, None),
        # Error State (None passed for dict causes AttributeError/TypeError on get())
        ("mock_idea_data", None, None, AttributeError),
    ],
)
def test_target_function_behavior(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    idea_fixture: str,
    scaffold_fixture: str | None,
    fm_fixture: str | None,
    expected: type[Exception] | None,
) -> None:
    # 1. Setup Data
    idea_data = request.getfixturevalue(idea_fixture)
    scaffold = request.getfixturevalue(scaffold_fixture) if scaffold_fixture else None
    feature_maps = request.getfixturevalue(fm_fixture) if fm_fixture else None

    # 2. Setup Mocks (Namespace Verified)
    # Using builtins.print because reporter.py imports print implicitly
    mock_print = mocker.patch("builtins.print")
    # Patch print_panel within src.utils.reporter because it's imported in the module/called by function
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)

    # 3. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)  # type: ignore
    else:
        result = print_demo_report(idea_data, scaffold, feature_maps)  # type: ignore
        assert result == expected

        # Verify Side Effects
        assert mock_print_panel.call_count >= 1
        assert mock_print.call_count >= 1
