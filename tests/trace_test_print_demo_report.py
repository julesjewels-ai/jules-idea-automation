from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.utils.reporter import print_demo_report

# FIXME: Verify patch path
# print_panel is used internally in src.utils.reporter
PATCH_TARGET_PRINT_PANEL = "src.utils.reporter.print_panel"


@pytest.fixture
def happy_path_context() -> dict[str, Any]:
    return {
        "idea_data": {"title": "Test App"},
        "scaffold": {
            "files": [{"path": "main.py", "description": "Entry point"}, {"path": "utils.py"}],
            "requirements": ["pytest", "pydantic"],
            "run_command": "python main.py",
        },
        "feature_maps": {
            "mvp_features": [
                {"name": "Auth", "priority": "High"},
                {"name": "DB", "priority": "Medium"},
                {"name": "UI", "priority": "Low"},
                {"name": "API", "priority": "High"},
                {"name": "Logs", "priority": "Medium"},
                {"name": "Metrics", "priority": "Low"},
            ],
            "production_features": [
                {"name": "Cache", "priority": "Medium"},
                {"name": "Queue", "priority": "High"},
                {"name": "CDN", "priority": "Low"},
                {"name": "WAF", "priority": "High"},
            ],
        },
    }


@pytest.fixture
def edge_case_context() -> dict[str, Any]:
    return {"idea_data": {"title": "Minimal App"}, "scaffold": {}, "feature_maps": None}


@pytest.fixture
def error_state_context() -> dict[str, Any]:
    return {
        "idea_data": {"title": "Error App"},
        "scaffold": None,  # Will cause AttributeError on .get()
        "feature_maps": None,
    }


@pytest.mark.parametrize(
    "context_fixture, expected",
    [
        ("happy_path_context", "success"),
        ("edge_case_context", "success"),
        ("error_state_context", AttributeError),
    ],
)
def test_print_demo_report_behavior(
    request: pytest.FixtureRequest, mocker: MockerFixture, context_fixture: str, expected: str | type[Exception]
) -> None:
    # 1. Setup Mocks
    mock_print_panel = mocker.patch(PATCH_TARGET_PRINT_PANEL, autospec=True)
    mock_print = mocker.patch("builtins.print", autospec=True)

    # Extract parameterized fixture data
    context = request.getfixturevalue(context_fixture)

    idea_data = context["idea_data"]
    scaffold = context["scaffold"]
    feature_maps = context["feature_maps"]

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_data, scaffold, feature_maps)
    else:
        print_demo_report(idea_data, scaffold, feature_maps)

        # Verify Side Effects
        assert mock_print_panel.call_count >= 1
        assert mock_print.call_count >= 1
