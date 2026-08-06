"""Markdown summary reporting for workflow execution."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.core.events import DomainEvent, WorkflowCompleted, WorkflowStarted
from src.core.interfaces import EventHandler
from src.services.jules import JulesClient
from src.utils.reporter import format_duration

logger = logging.getLogger(__name__)


class MarkdownSummaryGenerator(EventHandler):
    """Generates a Markdown summary of the session workflow execution."""

    def __init__(self, jules_client: JulesClient, output_dir: str = "reports") -> None:
        """Initialize the Markdown summary generator.

        Args:
        ----
            jules_client: The Jules client to fetch session activities.
            output_dir: The directory to write summary reports to.

        """
        self.jules_client = jules_client
        self.output_dir = Path(output_dir)
        self._start_times: dict[str, float] = {}

    def handle(self, event: Any) -> None:
        """Handle domain events to track and generate summaries.

        Args:
        ----
            event: The domain event to handle.

        """
        if not isinstance(event, DomainEvent):
            return

        if isinstance(event, WorkflowStarted):
            self._start_times[event.idea_slug] = event.timestamp
            logger.debug(f"Recorded start time for {event.idea_slug}")
        elif isinstance(event, WorkflowCompleted):
            self._generate_summary(event)

    def _generate_summary(self, event: WorkflowCompleted) -> None:
        """Generate and write the Markdown summary.

        Args:
        ----
            event: The WorkflowCompleted event containing project details.

        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            report_path = self.output_dir / f"{event.idea_slug}_summary.md"

            start_time = self._start_times.get(event.idea_slug, event.timestamp)
            duration_secs = int(event.timestamp - start_time)
            duration_str = format_duration(duration_secs)

            lines = [
                f"# Project Summary: {event.idea_title}",
                "",
                f"**Slug:** `{event.idea_slug}`",
                f"**Repository:** {event.repo_url}",
                f"**Duration:** {duration_str}",
                "",
            ]

            if event.session_id:
                lines.append("## Jules Session")
                lines.append("")
                lines.append(f"**Session ID:** `{event.session_id}`")
                lines.append(f"**URL:** {event.session_url}")
                lines.append("")

                try:
                    activities_data = self.jules_client.list_activities(event.session_id, page_size=100)
                    activities = activities_data.get("activities", [])
                    if activities:
                        lines.append("### Activity Log")
                        lines.append("")
                        for act in activities:
                            desc = str(act)
                            lines.append(f"- {desc}")
                        lines.append("")
                    else:
                        lines.append("*(No activity found for this session)*")
                        lines.append("")
                except Exception as e:
                    logger.warning(f"Could not fetch activities for summary: {e}")
                    lines.append(f"*(Error fetching activities: {e})*")
                    lines.append("")
            else:
                lines.append("*(No Jules session created for this workflow)*")
                lines.append("")

            report_path.write_text("\n".join(lines), encoding="utf-8")
            logger.debug(f"Generated Markdown summary at {report_path}")

        except Exception as e:
            logger.error(f"Failed to generate markdown summary: {e}", exc_info=True)
