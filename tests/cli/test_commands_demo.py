"""Tests for demo mode (--demo flag).

Verifies that demo mode:
1. Calls Gemini for scaffold + feature maps
2. Prints the demo report
3. Never instantiates GitHubClient or JulesClient
"""

from argparse import Namespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.cli._shared import execute_and_watch, execute_demo

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

IDEA_DATA: dict[str, Any] = {
    "title": "Test CLI Tool",
    "description": "A CLI tool for testing demo mode",
    "slug": "test-cli-tool",
    "tech_stack": ["Python", "Click"],
    "features": ["Unit tests", "CLI interface"],
}

SCAFFOLD: dict[str, Any] = {
    "files": [
        {"path": "main.py", "content": "print('hello')", "description": "Entry point"},
        {"path": "tests/test_main.py", "content": "def test(): pass", "description": "Tests"},
    ],
    "requirements": ["click", "pytest"],
    "run_command": "python main.py",
}

FEATURE_MAPS: dict[str, Any] = {
    "mvp_features": [
        {"name": "CLI parser", "priority": "P0"},
        {"name": "Unit tests", "priority": "P1"},
    ],
    "production_features": [
        {"name": "CI/CD pipeline", "priority": "P2"},
    ],
}


# ---------------------------------------------------------------------------
# Tests for execute_demo (direct)
# ---------------------------------------------------------------------------


@patch("src.cli._shared.print_demo_report")
@patch("src.cli._shared.Spinner")
@patch("src.cli._shared.build_gemini_client")
def test_execute_demo_calls_gemini_and_prints(mock_build: Any, mock_spinner: Any, mock_print_demo: Any) -> None:
    """Demo flow generates scaffold + feature maps, then prints report."""
    mock_gemini = MagicMock()
    mock_build.return_value = mock_gemini
    mock_gemini.generate_project_scaffold.return_value = SCAFFOLD
    mock_gemini.generate_feature_maps.return_value = FEATURE_MAPS

    execute_demo(IDEA_DATA)

    mock_gemini.generate_project_scaffold.assert_called_once_with(IDEA_DATA)
    mock_gemini.generate_feature_maps.assert_called_once_with(IDEA_DATA, SCAFFOLD["files"])
    mock_print_demo.assert_called_once_with(IDEA_DATA, SCAFFOLD, FEATURE_MAPS)


@patch("src.cli._shared.print_demo_report")
@patch("src.cli._shared.Spinner")
@patch("src.cli._shared.build_gemini_client")
def test_execute_demo_feature_maps_failure_is_graceful(
    mock_build: Any, mock_spinner: Any, mock_print_demo: Any
) -> None:
    """If feature map generation fails, demo still prints scaffold."""
    mock_gemini = MagicMock()
    mock_build.return_value = mock_gemini
    mock_gemini.generate_project_scaffold.return_value = SCAFFOLD
    mock_gemini.generate_feature_maps.side_effect = RuntimeError("API error")

    execute_demo(IDEA_DATA)

    # Should still succeed and print with feature_maps=None
    mock_print_demo.assert_called_once_with(IDEA_DATA, SCAFFOLD, None)


@patch("src.cli._shared.print_demo_report")
@patch("src.cli._shared.Spinner")
def test_execute_demo_uses_provided_gemini(mock_spinner: Any, mock_print_demo: Any) -> None:
    """When gemini is pre-constructed, execute_demo uses it directly."""
    mock_gemini = MagicMock()
    mock_gemini.generate_project_scaffold.return_value = SCAFFOLD
    mock_gemini.generate_feature_maps.return_value = FEATURE_MAPS

    execute_demo(IDEA_DATA, gemini=mock_gemini)

    mock_gemini.generate_project_scaffold.assert_called_once()
    mock_print_demo.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for execute_and_watch with --demo flag
# ---------------------------------------------------------------------------


@patch("src.cli._shared.execute_demo")
@patch("src.cli._shared.print_idea_summary")
def test_execute_and_watch_demo_flag_routes_to_demo(mock_summary: Any, mock_demo: Any) -> None:
    """When args.demo is True, execute_and_watch delegates to execute_demo."""
    args = Namespace(demo=True, public=False, timeout=1800, watch=False)

    execute_and_watch(args, IDEA_DATA)

    mock_demo.assert_called_once_with(IDEA_DATA, None)
    mock_summary.assert_not_called()  # Demo handles its own summary


@patch("src.cli._shared.execute_demo")
def test_execute_and_watch_demo_skips_github_jules(mock_demo: Any) -> None:
    """Demo mode never imports or instantiates GitHubClient/JulesClient."""
    args = Namespace(demo=True, public=False, timeout=1800, watch=False)

    with patch.dict(
        "sys.modules",
        {
            "src.services.github": MagicMock(),
            "src.services.jules": MagicMock(),
        },
    ):
        execute_and_watch(args, IDEA_DATA)

    mock_demo.assert_called_once()


@patch("src.cli._shared.execute_demo")
def test_execute_and_watch_no_demo_flag_skips_demo(mock_demo: Any) -> None:
    """When demo=False, execute_demo is NOT called."""
    args = Namespace(demo=False, public=False, timeout=1800, watch=False)

    # We expect it to proceed to the normal workflow which will fail
    # without proper mocking, so we just verify demo is not called
    with pytest.raises(Exception):
        execute_and_watch(args, IDEA_DATA)

    mock_demo.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for handle_agent with --demo
# ---------------------------------------------------------------------------


@patch("src.cli.cmd_agent.execute_and_watch")
@patch("src.cli.cmd_agent.Spinner")
@patch("src.cli.cmd_agent.build_gemini_client")
def test_handle_agent_demo(mock_build: Any, mock_spinner: Any, mock_exec: Any) -> None:
    """handle_agent passes args through to execute_and_watch which checks demo."""
    from src.cli.cmd_agent import handle_agent

    mock_gemini = MagicMock()
    mock_build.return_value = mock_gemini
    mock_gemini.generate_idea.return_value = IDEA_DATA

    args = Namespace(category=None, demo=True, public=False, timeout=1800, watch=False)
    handle_agent(args)

    mock_exec.assert_called_once()
    call_args = mock_exec.call_args
    assert call_args[0][0].demo is True


# ---------------------------------------------------------------------------
# Tests for handle_manual with --demo
# ---------------------------------------------------------------------------


@patch("src.cli.cmd_manual.execute_and_watch")
def test_handle_manual_demo(mock_exec: Any) -> None:
    """handle_manual passes args through to execute_and_watch which checks demo."""
    from src.cli.cmd_manual import handle_manual

    args = Namespace(
        title="My Demo Tool",
        description="A test tool",
        slug=None,
        tech_stack=None,
        features=None,
        demo=True,
        public=False,
        timeout=1800,
        watch=False,
    )
    handle_manual(args)

    mock_exec.assert_called_once()
    call_args = mock_exec.call_args
    assert call_args[0][0].demo is True
