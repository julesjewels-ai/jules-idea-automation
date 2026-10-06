import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report


@pytest.fixture
def mock_context() -> dict:
    return {
        "idea_data": {
            "title": "Test App",
            "description": "Desc",
            "slug": "test-app",
            "tech_stack": ["python"],
            "features": ["feature"],
        },
        "scaffold": {
            "files": [{"path": "main.py", "description": "Main file"}],
            "requirements": ["pytest"],
            "run_command": "python main.py",
        },
        "feature_maps": {
            "mvp_features": [{"name": "Auth", "priority": "P0"}],
            "production_features": [{"name": "CI/CD", "priority": "P1"}],
        },
    }


@pytest.fixture
def empty_context() -> dict:
    return {"idea_data": {"title": "Empty App"}, "scaffold": {}, "feature_maps": {}}


@pytest.fixture
def error_context() -> dict:
    return {
        "idea_data": {"title": "Error App"},
        "scaffold": 123,  # Will cause AttributeError when `.get` is called or iteration issues
        "feature_maps": {"mvp_features": "invalid_mvp"},
    }


@pytest.mark.parametrize(
    "context_name, expected",
    [
        ("mock_context", None),  # Happy Path
        ("empty_context", None),  # Edge Case
        ("error_context", AttributeError),  # Error State
    ],
)
def test_print_demo_report_behavior(
    request: pytest.FixtureRequest, mocker: MockerFixture, context_name: str, expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The file `src/utils/reporter.py` natively uses builtins.print and print_panel.
    # It defines print_panel in the same file. Since we're importing `print_demo_report` from `src.utils.reporter`,
    # we patch `src.utils.reporter.print_panel` and `builtins.print`.
    mock_print = mocker.patch("builtins.print")
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel")

    # Dynamically load the correct fixture
    context = request.getfixturevalue(context_name)
    idea_data = context["idea_data"]
    scaffold = context["scaffold"]
    feature_maps = context.get("feature_maps")

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        result = print_demo_report(idea_data, scaffold, feature_maps)
        assert result == expected
        # Verify Side Effects
        assert mock_print_panel.called
        assert mock_print.called
