"""Reporting service implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.core.events import WorkflowCompleted
from src.core.interfaces import EventHandler, ReportStorage
from src.utils.errors import ReportError

logger = logging.getLogger(__name__)


class FileReportStorage(ReportStorage):
    """File-based report storage implementation."""

    def __init__(self, base_dir: str = ".reports") -> None:
        """Initialize the file report storage.

        Args:
        ----
            base_dir: The directory to store reports in.

        """
        self.base_dir = Path(base_dir)
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning("Failed to create report directory %s: %s", self.base_dir, e)

    def save(self, report_id: str, content: str) -> None:
        """Save the generated report content to a file.

        Args:
        ----
            report_id: A unique identifier for the report.
            content: The rendered report content.

        """
        report_file = self.base_dir / f"{report_id}.md"
        try:
            report_file.write_text(content, encoding="utf-8")
            logger.debug("Saved report to %s", report_file)
        except Exception as e:
            raise ReportError(f"Failed to save report to {report_file}: {e}") from e


class MarkdownReportHandler(EventHandler):
    """Handler that generates a markdown report on workflow completion."""

    def __init__(self, storage: ReportStorage) -> None:
        """Initialize the markdown report handler.

        Args:
        ----
            storage: The storage mechanism to use for reports.

        """
        self.storage = storage

    def handle(self, event: Any) -> None:
        """Handle an event by generating a markdown report.

        Args:
        ----
            event: The domain event to handle.

        """
        if not isinstance(event, WorkflowCompleted):
            logger.debug("MarkdownReportHandler ignored non-WorkflowCompleted event: %s", type(event))
            return

        try:
            content = self._generate_markdown(event)
            report_id = event.idea_slug
            self.storage.save(report_id, content)
        except Exception as e:
            raise ReportError(f"Failed to generate and save markdown report: {e}") from e

    def _generate_markdown(self, event: WorkflowCompleted) -> str:
        """Generate markdown content from a WorkflowCompleted event."""
        lines = [
            f"# Workflow Report: {event.idea_title}",
            "",
            f"**Slug:** `{event.idea_slug}`",
            f"**Repository URL:** {event.repo_url}",
            "",
        ]

        if event.session_id:
            lines.extend(
                [
                    "## Jules Session",
                    "",
                    f"**Session ID:** `{event.session_id}`",
                    f"**Session URL:** {event.session_url}",
                ]
            )
        else:
            lines.extend(
                [
                    "## Jules Session",
                    "",
                    "Session was not created (source not indexed).",
                ]
            )

        return "\n".join(lines) + "\n"
