"""Reporting module for the Jules Automation Tool."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.core.events import WorkflowCompleted
from src.core.interfaces import EventHandler, ReportGenerator, ReportRepository
from src.utils.errors import ReportError

logger = logging.getLogger(__name__)


class FileReportRepository(ReportRepository):
    """File-based implementation of the ReportRepository protocol."""

    def __init__(self, output_dir: str | Path = "reports") -> None:
        """Initialize the repository.

        Args:
        ----
            output_dir: The directory where reports will be saved.

        """
        self.output_dir = Path(output_dir)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create reports directory {self.output_dir}: {e}")

    def save_report(self, slug: str, content: str) -> None:
        """Save a generated report to a Markdown file.

        Args:
        ----
            slug: The project slug.
            content: The report content.

        """
        file_path = self.output_dir / f"{slug}_report.md"
        try:
            file_path.write_text(content, encoding="utf-8")
            logger.debug(f"Saved report for {slug} to {file_path}")
        except OSError as e:
            raise ReportError(f"Failed to save report to {file_path}: {e}") from e


class MarkdownReportGenerator(ReportGenerator):
    """Generates a Markdown report from a WorkflowCompleted event."""

    def generate(self, event: Any) -> str:
        """Generate a Markdown report from the event.

        Args:
        ----
            event: The domain event to report on.

        Returns:
        -------
            The generated Markdown report as a string.

        """
        if not isinstance(event, WorkflowCompleted):
            raise ReportError(f"Expected WorkflowCompleted event, got {type(event)}")

        lines = [
            f"# Workflow Report: {event.idea_title}",
            "",
            "## Details",
            f"- **Slug**: {event.idea_slug}",
            f"- **Repository URL**: {event.repo_url}",
        ]

        if event.session_id:
            lines.extend(
                [
                    f"- **Jules Session ID**: {event.session_id}",
                    f"- **Jules Session URL**: {event.session_url or 'N/A'}",
                ]
            )
        else:
            lines.append("- **Jules Session**: N/A")

        lines.extend(["", "---", "*Report generated automatically by the Jules Automation Tool.*"])

        return "\n".join(lines)


class WorkflowReportingHandler(EventHandler):
    """Handler that coordinates generating and saving a report for a completed workflow."""

    def __init__(self, generator: ReportGenerator, repository: ReportRepository) -> None:
        """Initialize the handler.

        Args:
        ----
            generator: The service used to generate the report.
            repository: The service used to save the report.

        """
        self.generator = generator
        self.repository = repository

    def handle(self, event: Any) -> None:
        """Handle the event by generating and saving a report.

        Args:
        ----
            event: The domain event to handle.

        """
        if not isinstance(event, WorkflowCompleted):
            logger.debug(f"WorkflowReportingHandler ignored non-WorkflowCompleted event: {type(event)}")
            return

        try:
            content = self.generator.generate(event)
            self.repository.save_report(event.idea_slug, content)
        except ReportError as e:
            logger.error(f"Reporting failed for {event.idea_slug}: {e}")
            # We don't raise here to allow other handlers to run.
