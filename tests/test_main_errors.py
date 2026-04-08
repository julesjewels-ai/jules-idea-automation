"""Tests for main.py error handling: structured panels and --verbose traceback."""

from __future__ import annotations

import sys
from typing import Any, NamedTuple
from unittest.mock import patch

import pytest


class _RunResult(NamedTuple):
    exit_code: int
    out: str
    err: str


def _run_main_with_args(monkeypatch: Any, capsys: Any, args: list[str]) -> _RunResult:
    """Run main() with the given CLI args and return (exit_code, stdout, stderr).

    Captures stdout/stderr inside the function so callers don't need to call
    ``capsys.readouterr()`` themselves after every patch context.
    """
    monkeypatch.setattr(sys, "argv", ["main.py"] + args)
    from main import main  # noqa: PLC0415

    with pytest.raises(SystemExit) as exc_info:
        main()

    captured = capsys.readouterr()
    code = exc_info.value.code
    return _RunResult(int(code) if code is not None and str(code).isdigit() else 1, captured.out, captured.err)


class TestAppErrorHandler:
    """AppError subclasses should render a styled panel, not a raw traceback."""

    def test_app_error_renders_panel(self, monkeypatch: Any, capsys: Any) -> None:
        from src.utils.errors import ConfigurationError

        with patch(
            "main.dispatch_command",
            side_effect=ConfigurationError("token missing", tip="Set GITHUB_TOKEN"),
        ):
            result = _run_main_with_args(monkeypatch, capsys, ["agent"])

        assert result.exit_code == 1
        # Panel title and message should appear in stdout
        assert "Configuration Error" in result.out
        assert "token missing" in result.out
        assert "Set GITHUB_TOKEN" in result.out

    def test_app_error_no_traceback_without_verbose(self, monkeypatch: Any, capsys: Any) -> None:
        from src.utils.errors import GenerationError

        with patch("main.dispatch_command", side_effect=GenerationError("failed")):
            result = _run_main_with_args(monkeypatch, capsys, ["agent"])

        assert "Traceback" not in result.err

    def test_app_error_shows_traceback_with_verbose(self, monkeypatch: Any, capsys: Any) -> None:
        from src.utils.errors import GenerationError

        with patch("main.dispatch_command", side_effect=GenerationError("gen failed")):
            result = _run_main_with_args(monkeypatch, capsys, ["--verbose", "agent"])

        assert "Traceback" in result.err


class TestGenericExceptionHandler:
    """Bare Exceptions should also render a panel, not a plain stderr line."""

    def test_generic_exception_renders_panel(self, monkeypatch: Any, capsys: Any) -> None:
        with patch("main.dispatch_command", side_effect=RuntimeError("something broke")):
            result = _run_main_with_args(monkeypatch, capsys, ["agent"])

        assert result.exit_code == 1
        assert "Unexpected Error" in result.out
        assert "something broke" in result.out

    def test_generic_exception_no_traceback_without_verbose(self, monkeypatch: Any, capsys: Any) -> None:
        with patch("main.dispatch_command", side_effect=RuntimeError("boom")):
            result = _run_main_with_args(monkeypatch, capsys, ["agent"])

        assert "Traceback" not in result.err
        # Should hint the user about --verbose
        assert "--verbose" in result.err

    def test_generic_exception_shows_traceback_with_verbose(self, monkeypatch: Any, capsys: Any) -> None:
        with patch("main.dispatch_command", side_effect=RuntimeError("verbose boom")):
            result = _run_main_with_args(monkeypatch, capsys, ["--verbose", "agent"])

        assert "Traceback" in result.err
        assert "RuntimeError" in result.err
        assert "verbose boom" in result.err

    def test_generic_exception_no_message_shows_class_name(self, monkeypatch: Any, capsys: Any) -> None:
        """Exception() with no message should fall back to the class name in the panel."""
        with patch("main.dispatch_command", side_effect=ValueError()):
            result = _run_main_with_args(monkeypatch, capsys, ["agent"])

        assert result.exit_code == 1
        # Empty str(e) falls back to "ValueError" as panel content
        assert "ValueError" in result.out


class TestParserVerboseFlag:
    """--verbose should be recognised by create_parser() at the root level."""

    def test_verbose_flag_defaults_false(self) -> None:
        from src.cli.parser import create_parser

        parser = create_parser()
        args = parser.parse_args(["agent"])
        assert args.verbose is False

    def test_verbose_flag_set_true(self) -> None:
        from src.cli.parser import create_parser

        parser = create_parser()
        args = parser.parse_args(["--verbose", "agent"])
        assert args.verbose is True

    def test_verbose_flag_before_subcommand(self) -> None:
        """--verbose must appear before the subcommand (argparse global flag position)."""
        from src.cli.parser import create_parser

        parser = create_parser()
        args = parser.parse_args(["--verbose", "website", "--url", "http://example.com"])
        assert args.verbose is True


class TestFormatErrorTitle:
    """_format_error_title should produce readable titles from class names."""

    def test_simple_error(self) -> None:
        from main import _format_error_title
        from src.utils.errors import ConfigurationError

        assert _format_error_title(ConfigurationError("x")) == "Configuration Error"

    def test_multi_word_error(self) -> None:
        from main import _format_error_title
        from src.utils.errors import GitHubApiError

        assert _format_error_title(GitHubApiError("x")) == "Git Hub Api Error"

    def test_runtime_error(self) -> None:
        from main import _format_error_title

        assert _format_error_title(RuntimeError("x")) == "Runtime Error"
