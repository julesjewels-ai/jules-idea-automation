"""Automated reporting service."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Generic

from src.core.interfaces import ReportGenerator, ReportStorage, T_Report
from src.utils.errors import AppError

logger = logging.getLogger(__name__)


class ReportingError(AppError):
    """Base class for reporting errors."""


class MarkdownReportGenerator(ReportGenerator[str]):
    """Generates Markdown reports from workflow data."""

    def generate(self, data: dict[str, Any]) -> str:
        """Generate a Markdown report from the provided data."""
        try:
            # Assuming data is the dumped WorkflowResult or a dictionary containing relevant info
            idea = data.get("idea", {})
            title = idea.get("title", "Untitled")
            description = idea.get("description", "No description provided.")
            slug = idea.get("slug", "unknown-slug")
            tech_stack = ", ".join(idea.get("tech_stack", [])) or "None specified"
            features = "\n".join(f"- {f}" for f in idea.get("features", [])) or "None specified"

            repo_url = data.get("repo_url", "N/A")
            session_id = data.get("session_id", "N/A")
            session_url = data.get("session_url", "N/A")
            pr_url = data.get("pr_url", "N/A")

            report = f"# {title}\n\n"
            report += f"**Slug**: {slug}\n\n"
            report += f"## Description\n{description}\n\n"
            report += f"## Tech Stack\n{tech_stack}\n\n"
            report += f"## Features\n{features}\n\n"
            report += "## Workflow Details\n"
            report += f"- **Repository**: [Link]({repo_url})\n"
            report += f"- **Jules Session ID**: {session_id}\n"
            report += f"- **Jules Session URL**: [Link]({session_url})\n"
            if pr_url and pr_url != "N/A":
                report += f"- **Pull Request**: [Link]({pr_url})\n"

            return report
        except Exception as e:
            raise ReportingError(f"Failed to generate Markdown report: {e}")


class FileReportStorage(ReportStorage[str]):
    """Stores reports as local files."""

    def __init__(self, output_dir: Path | str = "reports") -> None:
        """Initialize the storage with an output directory."""
        self.output_dir = Path(output_dir)

    def save(self, report: str, identifier: str) -> str:
        """Save a report to the output directory."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            # Ensure the identifier acts as a safe filename
            safe_id = "".join(c for c in identifier if c.isalnum() or c in ("-", "_")).rstrip()
            filename = f"{safe_id}_report.md"
            filepath = self.output_dir / filename
            filepath.write_text(report, encoding="utf-8")
            logger.info("Report saved to %s", filepath)
            return str(filepath)
        except Exception as e:
            raise ReportingError(f"Failed to save report to file: {e}")


class AutomatedReportingService(Generic[T_Report]):
    """Service to orchestrate report generation and storage."""

    def __init__(self, generator: ReportGenerator[T_Report], storage: ReportStorage[T_Report]) -> None:
        """Initialize with a generator and a storage mechanism."""
        self.generator = generator
        self.storage = storage

    def create_and_store_report(self, data: dict[str, Any], identifier: str) -> str:
        """Generate a report and store it.

        Args:
        ----
            data: The data to report on.
            identifier: A unique identifier for the report.

        Returns:
        -------
            The location of the stored report.

        """
        try:
            report = self.generator.generate(data)
            location = self.storage.save(report, identifier)
            return location
        except Exception as e:
            if isinstance(e, ReportingError):
                raise
            raise ReportingError(f"Automated reporting failed: {e}")
