import pytest
from pytest_mock import MockerFixture
from src.utils.reporter import print_demo_report

@pytest.fixture
def mock_context() -> dict:
    return {
        "title": "Test Idea",
        "description": "Test Desc"
    }

@pytest.fixture
def mock_scaffold() -> dict:
    return {
        "files": [{"path": "main.py", "description": "Main entry point"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }

@pytest.fixture
def mock_feature_maps() -> dict:
    return {
        "mvp_features": [
            {"name": "F1", "priority": "High"},
            {"name": "F2", "priority": "High"},
            {"name": "F3", "priority": "High"},
            {"name": "F4", "priority": "High"},
            {"name": "F5", "priority": "High"},
            {"name": "F6", "priority": "High"},
        ],
        "production_features": [
            {"name": "P1", "priority": "Low"},
            {"name": "P2", "priority": "Low"},
            {"name": "P3", "priority": "Low"},
            {"name": "P4", "priority": "Low"},
        ]
    }

@pytest.mark.parametrize("scenario, expected", [
    ("happy_path", None),
    ("edge_case", None),
    ("error_state", AttributeError),
])
def test_print_demo_report_behavior(
    mocker: MockerFixture,
    mock_context: dict,
    mock_scaffold: dict,
    mock_feature_maps: dict,
    scenario: str,
    expected: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # Both print and print_panel are used inside src.utils.reporter.
    mock_print_panel = mocker.patch("src.utils.reporter.print_panel", autospec=True)
    mock_print = mocker.patch("builtins.print")

    if scenario == "happy_path":
        idea_val = mock_context
        scaffold_val = mock_scaffold
        fm_val = mock_feature_maps
    elif scenario == "edge_case":
        idea_val = mock_context
        scaffold_val = {}
        fm_val = {}
    elif scenario == "error_state":
        idea_val = mock_context
        scaffold_val = None  # type: ignore
        fm_val = None
    else:
        raise ValueError(f"Unknown scenario {scenario}")

    # 2. Execution & Validation
    if expected is not None and issubclass(expected, Exception):
        with pytest.raises(expected):
            print_demo_report(idea_val, scaffold_val, fm_val)
    else:
        result = print_demo_report(idea_val, scaffold_val, fm_val)
        assert result == expected
        mock_print_panel.assert_called()
        mock_print.assert_called()
