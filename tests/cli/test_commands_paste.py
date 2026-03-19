"""Tests for the paste command and website --content flag."""

from __future__ import annotations

from argparse import Namespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.cli.commands import _read_clipboard, _read_paste_content, handle_paste, handle_website

# --- _read_clipboard tests ---


@patch("src.cli.commands.subprocess.run")
def test_read_clipboard_success(mock_run: Any) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="clipboard content here", stderr="")
    result = _read_clipboard()
    assert result == "clipboard content here"
    mock_run.assert_called_once_with(["pbpaste"], capture_output=True, text=True, timeout=5)


@patch("src.cli.commands.subprocess.run")
def test_read_clipboard_failure(mock_run: Any) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="some error")
    with pytest.raises(RuntimeError, match="pbpaste failed"):
        _read_clipboard()


@patch("src.cli.commands.subprocess.run", side_effect=FileNotFoundError)
def test_read_clipboard_not_available(mock_run: Any) -> None:
    with pytest.raises(RuntimeError, match="pbpaste"):
        _read_clipboard()


# --- _read_paste_content tests ---


LONG_CONTENT = "A" * 250  # Above MIN_CONTENT_LENGTH (200)
SHORT_CONTENT = "A" * 50  # Below MIN_CONTENT_LENGTH


@patch("src.cli.commands._read_clipboard", return_value=LONG_CONTENT)
def test_read_paste_content_clipboard(mock_clip: Any) -> None:
    args = Namespace(clipboard=True, file_path=None, content_source=None)
    result = _read_paste_content(args)
    assert result == LONG_CONTENT
    mock_clip.assert_called_once()


@patch("src.cli.commands._read_clipboard", return_value=SHORT_CONTENT)
def test_read_paste_content_clipboard_too_short(mock_clip: Any) -> None:
    args = Namespace(clipboard=True, file_path=None, content_source=None)
    with pytest.raises(SystemExit):
        _read_paste_content(args)


def test_read_paste_content_file(tmp_path: Any) -> None:
    test_file = tmp_path / "test_content.txt"
    test_file.write_text(LONG_CONTENT, encoding="utf-8")

    args = Namespace(clipboard=False, file_path=str(test_file), content_source=None)
    result = _read_paste_content(args)
    assert result == LONG_CONTENT


def test_read_paste_content_file_not_found() -> None:
    args = Namespace(clipboard=False, file_path="/nonexistent/file.txt", content_source=None)
    with pytest.raises(SystemExit):
        _read_paste_content(args)


@patch("sys.stdin")
def test_read_paste_content_stdin_pipe(mock_stdin: Any) -> None:
    mock_stdin.read.return_value = LONG_CONTENT
    args = Namespace(clipboard=False, file_path=None, content_source="-")
    result = _read_paste_content(args)
    assert result == LONG_CONTENT


@patch("sys.stdin")
def test_read_paste_content_interactive(mock_stdin: Any) -> None:
    mock_stdin.read.return_value = LONG_CONTENT
    args = Namespace(clipboard=False, file_path=None, content_source=None)
    result = _read_paste_content(args)
    assert result == LONG_CONTENT


# --- handle_paste tests ---


@patch("src.cli.commands._execute_and_watch")
@patch("src.cli.commands.Spinner")
@patch("src.services.gemini.GeminiClient")
@patch("src.services.cache.FileCacheProvider")
@patch("src.cli.commands._read_paste_content", return_value=LONG_CONTENT)
def test_handle_paste_calls_gemini(
    mock_read: Any,
    mock_cache_class: Any,
    mock_gemini_class: Any,
    mock_spinner: Any,
    mock_execute: Any,
) -> None:
    mock_gemini = mock_gemini_class.return_value
    mock_gemini.extract_idea_from_text.return_value = {"title": "Test", "description": "Test idea"}

    args = Namespace(clipboard=False, file_path=None, content_source=None, public=False, timeout=1800, watch=False)
    handle_paste(args)

    mock_read.assert_called_once_with(args)
    mock_gemini.extract_idea_from_text.assert_called_once_with(LONG_CONTENT)
    mock_execute.assert_called_once()


# --- handle_website --content tests ---


@patch("src.cli.commands._execute_and_watch")
@patch("src.cli.commands.Spinner")
@patch("src.services.gemini.GeminiClient")
@patch("src.services.cache.FileCacheProvider")
def test_handle_website_with_content_skips_scraper(
    mock_cache_class: Any,
    mock_gemini_class: Any,
    mock_spinner: Any,
    mock_execute: Any,
) -> None:
    mock_gemini = mock_gemini_class.return_value
    mock_gemini.extract_idea_from_text.return_value = {"title": "Test", "description": "Test idea"}

    args = Namespace(content=LONG_CONTENT, url=None, public=False, timeout=1800, watch=False)

    with patch("src.cli.commands.scrape_text", side_effect=AssertionError("scraper should not be called")) as _:
        handle_website(args)

    mock_gemini.extract_idea_from_text.assert_called_once_with(LONG_CONTENT)
    mock_execute.assert_called_once()


@patch("src.cli.commands._execute_and_watch")
@patch("src.cli.commands.Spinner")
@patch("src.services.gemini.GeminiClient")
@patch("src.services.cache.FileCacheProvider")
def test_handle_website_with_url_uses_scraper(
    mock_cache_class: Any,
    mock_gemini_class: Any,
    mock_spinner: Any,
    mock_execute: Any,
) -> None:
    mock_gemini = mock_gemini_class.return_value
    mock_gemini.extract_idea_from_text.return_value = {"title": "Test", "description": "Test idea"}

    args = Namespace(content=None, url="https://example.com", public=False, timeout=1800, watch=False)

    with patch("src.services.scraper.scrape_text", return_value=LONG_CONTENT):
        handle_website(args)

    mock_gemini.extract_idea_from_text.assert_called_once_with(LONG_CONTENT)
    mock_execute.assert_called_once()
