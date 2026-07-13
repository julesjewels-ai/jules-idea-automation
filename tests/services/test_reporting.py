"""Tests for the reporting service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.reporting import MarkdownReportGenerator
from src.utils.errors import ReportingError


def test_markdown_report_generator_export(tmp_path: Path) -> None:
    """Test that the MarkdownReportGenerator correctly exports a workflow result."""
    generator = MarkdownReportGenerator()

    idea = IdeaResponse(
        title="Test Idea",
        description="A great test idea.",
        slug="test-idea",
        tech_stack=["Python", "Pytest"],
        features=["Fast", "Reliable"],
    )

    result = WorkflowResult(
        idea=idea,
        repo_url="https://github.com/testuser/test-idea",
        session_id="test-session-123",
        session_url="https://jules.google.com/session/123",
        pr_url="https://github.com/testuser/test-idea/pull/1",
    )

    with patch("src.services.reporting.Path.cwd", return_value=tmp_path):
        filepath_str = generator.export(result)

        filepath = Path(filepath_str)
        assert filepath.exists()
        assert filepath.name == "test-idea_summary.md"
        assert filepath.parent == tmp_path

        content = filepath.read_text(encoding="utf-8")
        assert "# Workflow Summary: Test Idea" in content
        assert "**Idea Slug:** `test-idea`" in content
        assert (
            "**Repository:** [https://github.com/testuser/test-idea](https://github.com/testuser/test-idea)" in content
        )
        assert "**Jules Session ID:** `test-session-123`" in content
        assert (
            "**Jules Session URL:** [https://jules.google.com/session/123](https://jules.google.com/session/123)"
            in content
        )
        assert (
            "**Pull Request:** [https://github.com/testuser/test-idea/pull/1](https://github.com/testuser/test-idea/pull/1)"
            in content
        )
        assert "**Description:** A great test idea." in content
        assert "- Python" in content
        assert "- Fast" in content


def test_markdown_report_generator_export_error(tmp_path: Path) -> None:
    """Test that an error is raised if the file cannot be written."""
    generator = MarkdownReportGenerator()

    idea = IdeaResponse(
        title="Test Idea",
        description="A great test idea.",
        slug="test-idea",
        tech_stack=[],
        features=[],
    )

    result = WorkflowResult(
        idea=idea,
        repo_url="https://github.com/testuser/test-idea",
    )

    with patch("src.services.reporting.Path.cwd", return_value=tmp_path):
        with patch("src.services.reporting.Path.write_text", side_effect=OSError("Permission denied")):
            with pytest.raises(ReportingError, match="Failed to generate Markdown report: Permission denied"):
                generator.export(result)
