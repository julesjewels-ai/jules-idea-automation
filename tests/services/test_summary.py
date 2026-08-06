"""Tests for the MarkdownSummaryGenerator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.events import WorkflowCompleted, WorkflowStarted
from src.services.summary import MarkdownSummaryGenerator


class TestMarkdownSummaryGenerator:
    """Test suite for MarkdownSummaryGenerator."""

    @pytest.fixture
    def mock_jules_client(self) -> MagicMock:
        """Provide a mocked JulesClient."""
        client = MagicMock()
        client.list_activities.return_value = {"activities": ["Activity 1", "Activity 2"]}
        return client

    @pytest.fixture
    def summary_generator(self, mock_jules_client: MagicMock, tmp_path: Path) -> MarkdownSummaryGenerator:
        """Provide a MarkdownSummaryGenerator using a temporary directory."""
        return MarkdownSummaryGenerator(jules_client=mock_jules_client, output_dir=str(tmp_path))

    def test_ignores_non_domain_events(self, summary_generator: MarkdownSummaryGenerator) -> None:
        """It should silently ignore non-domain events."""
        # This shouldn't crash or raise exceptions
        summary_generator.handle("not a domain event")

    def test_records_start_time(self, summary_generator: MarkdownSummaryGenerator) -> None:
        """It should record the start time when a WorkflowStarted event is received."""
        started_event = WorkflowStarted(
            event_id="evt-1",
            idea_title="Test App",
            idea_slug="test-app",
            timestamp=100.0,
        )
        summary_generator.handle(started_event)

        assert summary_generator._start_times["test-app"] == 100.0

    def test_generates_summary_with_session_and_activities(
        self, summary_generator: MarkdownSummaryGenerator, mock_jules_client: MagicMock, tmp_path: Path
    ) -> None:
        """It should generate a markdown file containing activities and duration."""
        # Seed the start time
        started_event = WorkflowStarted(
            event_id="evt-1",
            idea_title="Test App",
            idea_slug="test-app",
            timestamp=100.0,
        )
        summary_generator.handle(started_event)

        # Trigger completion
        completed_event = WorkflowCompleted(
            event_id="evt-2",
            idea_title="Test App",
            idea_slug="test-app",
            repo_url="https://github.com/user/test-app",
            session_id="session-123",
            session_url="https://jules.google.com/session-123",
            timestamp=165.0,  # 65 seconds duration
        )
        summary_generator.handle(completed_event)

        # Verify API was called
        mock_jules_client.list_activities.assert_called_once_with("session-123", page_size=100)

        # Verify file creation
        report_path = tmp_path / "test-app_summary.md"
        assert report_path.exists()

        content = report_path.read_text(encoding="utf-8")

        # Verify content details
        assert "# Project Summary: Test App" in content
        assert "**Slug:** `test-app`" in content
        assert "**Repository:** https://github.com/user/test-app" in content
        assert "**Duration:** 1m 5s" in content  # 65 seconds format

        # Verify Jules session details
        assert "## Jules Session" in content
        assert "**Session ID:** `session-123`" in content
        assert "**URL:** https://jules.google.com/session-123" in content

        # Verify activities
        assert "### Activity Log" in content
        assert "- Activity 1" in content
        assert "- Activity 2" in content

    def test_generates_summary_without_session(
        self, summary_generator: MarkdownSummaryGenerator, mock_jules_client: MagicMock, tmp_path: Path
    ) -> None:
        """It should generate a markdown file indicating no session was created."""
        completed_event = WorkflowCompleted(
            event_id="evt-2",
            idea_title="No Session App",
            idea_slug="no-session",
            repo_url="https://github.com/user/no-session",
            session_id=None,
            session_url=None,
            timestamp=200.0,
        )
        summary_generator.handle(completed_event)

        # API should not be called
        mock_jules_client.list_activities.assert_not_called()

        report_path = tmp_path / "no-session_summary.md"
        assert report_path.exists()

        content = report_path.read_text(encoding="utf-8")
        assert "# Project Summary: No Session App" in content
        assert "*(No Jules session created for this workflow)*" in content

    def test_generates_summary_when_activities_fetch_fails(
        self, summary_generator: MarkdownSummaryGenerator, mock_jules_client: MagicMock, tmp_path: Path
    ) -> None:
        """It should handle exceptions when fetching activities gracefully."""
        mock_jules_client.list_activities.side_effect = Exception("API error")

        completed_event = WorkflowCompleted(
            event_id="evt-3",
            idea_title="Error App",
            idea_slug="error-app",
            repo_url="https://github.com/user/error",
            session_id="session-456",
            session_url="https://jules.google.com/session-456",
            timestamp=300.0,
        )
        summary_generator.handle(completed_event)

        report_path = tmp_path / "error-app_summary.md"
        assert report_path.exists()

        content = report_path.read_text(encoding="utf-8")
        assert "## Jules Session" in content
        assert "*(Error fetching activities: API error)*" in content
