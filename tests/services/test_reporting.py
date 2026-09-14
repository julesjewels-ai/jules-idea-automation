"""Tests for the reporting service."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from src.core.events import WorkflowCompleted
from src.services.reporting import FileReportStorage, MarkdownReportHandler
from src.utils.errors import ReportError


def test_markdown_report_handler_success() -> None:
    """Test successful generation and saving of a markdown report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileReportStorage(base_dir=tmpdir)
        handler = MarkdownReportHandler(storage=storage)

        event = WorkflowCompleted(
            event_id="test-event-123",
            idea_title="Test Project",
            idea_slug="test-project",
            repo_url="https://github.com/user/test-project",
            session_id="session-123",
            session_url="https://jules.google.com/session-123",
        )

        handler.handle(event)

        report_file = Path(tmpdir) / "test-project.md"
        assert report_file.exists()

        content = report_file.read_text(encoding="utf-8")
        assert "# Workflow Report: Test Project" in content
        assert "**Slug:** `test-project`" in content
        assert "**Repository URL:** https://github.com/user/test-project" in content
        assert "## Jules Session" in content
        assert "**Session ID:** `session-123`" in content
        assert "**Session URL:** https://jules.google.com/session-123" in content


def test_markdown_report_handler_no_session() -> None:
    """Test report generation when session details are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileReportStorage(base_dir=tmpdir)
        handler = MarkdownReportHandler(storage=storage)

        event = WorkflowCompleted(
            event_id="test-event-123",
            idea_title="Test Project",
            idea_slug="test-project",
            repo_url="https://github.com/user/test-project",
            session_id=None,
            session_url=None,
        )

        handler.handle(event)

        report_file = Path(tmpdir) / "test-project.md"
        assert report_file.exists()

        content = report_file.read_text(encoding="utf-8")
        assert "Session was not created (source not indexed)." in content
        assert "session-123" not in content


def test_markdown_report_handler_ignores_other_events() -> None:
    """Test that the handler ignores non-WorkflowCompleted events."""

    class DummyEvent:
        pass

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileReportStorage(base_dir=tmpdir)
        handler = MarkdownReportHandler(storage=storage)

        handler.handle(DummyEvent())

        # Directory should be empty
        assert list(Path(tmpdir).iterdir()) == []


def test_file_report_storage_save_error(monkeypatch: Any) -> None:
    """Test that ReportError is raised when saving fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileReportStorage(base_dir=tmpdir)

        # Force a write error by patching write_text
        def mock_write_text(*args: Any, **kwargs: Any) -> None:
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(ReportError) as excinfo:
            storage.save("test-report", "content")

        assert "Failed to save report" in str(excinfo.value)
