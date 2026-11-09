"""Tests for the reporting service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.events import WorkflowCompleted
from src.services.reporting import (
    FileReportRepository,
    MarkdownReportGenerator,
    WorkflowReportingHandler,
)
from src.utils.errors import ReportError


@pytest.fixture
def workflow_completed_event() -> WorkflowCompleted:
    return WorkflowCompleted(
        event_id="test-event-id",
        idea_title="Test Idea",
        idea_slug="test-idea",
        repo_url="https://github.com/test/test-idea",
        session_id="session-123",
        session_url="https://jules.google.com/session/123",
    )


def test_markdown_report_generator(workflow_completed_event: WorkflowCompleted) -> None:
    generator = MarkdownReportGenerator()
    report = generator.generate(workflow_completed_event)

    assert "# Workflow Report: Test Idea" in report
    assert "- **Slug**: test-idea" in report
    assert "- **Repository URL**: https://github.com/test/test-idea" in report
    assert "- **Jules Session ID**: session-123" in report
    assert "- **Jules Session URL**: https://jules.google.com/session/123" in report


def test_markdown_report_generator_invalid_event() -> None:
    generator = MarkdownReportGenerator()
    with pytest.raises(ReportError, match="Expected WorkflowCompleted event"):
        generator.generate(MagicMock())  # pyre-ignore[6]


def test_file_report_repository(tmp_path: Path) -> None:
    repository = FileReportRepository(output_dir=tmp_path)
    repository.save_report("test-slug", "Test Content")

    report_path = tmp_path / "test-slug_report.md"
    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8") == "Test Content"


def test_workflow_reporting_handler(workflow_completed_event: WorkflowCompleted) -> None:
    mock_generator = MagicMock()
    mock_generator.generate.return_value = "Mocked Report"
    mock_repository = MagicMock()

    handler = WorkflowReportingHandler(mock_generator, mock_repository)
    handler.handle(workflow_completed_event)

    mock_generator.generate.assert_called_once_with(workflow_completed_event)
    mock_repository.save_report.assert_called_once_with("test-idea", "Mocked Report")


def test_workflow_reporting_handler_integration(tmp_path: Path, workflow_completed_event: WorkflowCompleted) -> None:
    generator = MarkdownReportGenerator()
    repository = FileReportRepository(output_dir=tmp_path)
    handler = WorkflowReportingHandler(generator, repository)

    handler.handle(workflow_completed_event)

    report_path = tmp_path / "test-idea_report.md"
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")

    assert "# Workflow Report: Test Idea" in report
    assert "test-idea" in report
