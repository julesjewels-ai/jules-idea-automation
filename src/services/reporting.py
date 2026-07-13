"""Report generation service for the Jules Automation Tool."""

from __future__ import annotations

import logging
from pathlib import Path

from src.core.interfaces import ReportGenerator
from src.core.models import WorkflowResult
from src.utils.errors import ReportingError

logger = logging.getLogger(__name__)


class MarkdownReportGenerator(ReportGenerator):
    """Generates a Markdown summary file for a completed workflow."""

    def export(self, result: WorkflowResult) -> str:
        """Generate a Markdown report from a workflow result.

        Args:
        ----
            result: The completed workflow result.

        Returns:
        -------
            The file path where the report was saved.

        Raises:
        ------
            ReportingError: If the report generation or saving fails.

        """
        try:
            filename = f"{result.idea.slug}_summary.md"
            filepath = Path.cwd() / filename

            lines: list[str] = [
                f"# Workflow Summary: {result.idea.title}",
                "",
                f"**Idea Slug:** `{result.idea.slug}`",
                f"**Repository:** [{result.repo_url}]({result.repo_url})",
                "",
            ]

            if result.session_id:
                lines.append(f"**Jules Session ID:** `{result.session_id}`")
                if result.session_url:
                    lines.append(f"**Jules Session URL:** [{result.session_url}]({result.session_url})")
                if result.pr_url:
                    lines.append(f"**Pull Request:** [{result.pr_url}]({result.pr_url})")
                lines.append("")

            lines.extend(
                [
                    "## Idea Details",
                    "",
                    f"**Description:** {result.idea.description}",
                    "",
                ]
            )

            if result.idea.tech_stack:
                lines.append("**Tech Stack:**")
                for tech in result.idea.tech_stack:
                    lines.append(f"- {tech}")
                lines.append("")

            if result.idea.features:
                lines.append("**Features:**")
                for feature in result.idea.features:
                    lines.append(f"- {feature}")
                lines.append("")

            content = "\n".join(lines)

            filepath.write_text(content, encoding="utf-8")
            logger.debug(f"Markdown report generated at {filepath}")

            return str(filepath)

        except Exception as e:
            raise ReportingError(
                f"Failed to generate Markdown report: {e}", tip="Check file system permissions."
            ) from e
