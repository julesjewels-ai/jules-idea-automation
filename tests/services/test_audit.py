"""Unit tests for JsonFileAuditLogger."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.events import WorkflowCompleted, WorkflowStarted
from src.services.audit import JsonFileAuditLogger
from src.utils.errors import AuditError

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _started_event() -> WorkflowStarted:
    return WorkflowStarted(
        event_id="evt-001",
        idea_title="Test Idea",
        idea_slug="test-idea",
        category="cli_tool",
    )


def _completed_event() -> WorkflowCompleted:
    return WorkflowCompleted(
        event_id="evt-002",
        idea_title="Test Idea",
        idea_slug="test-idea",
        repo_url="https://github.com/testuser/test-idea",
        session_id="session-123",
        session_url="https://jules.example.com/session/123",
    )


from typing import Any


def _read_lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# TestHappyPath
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_single_event_creates_file(self, tmp_path: Path) -> None:
        """handle() creates the log file and writes one JSONL line."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        logger.handle(_started_event())

        assert log_file.exists()
        lines = _read_lines(log_file)
        assert len(lines) == 1

    def test_event_type_field_injected(self, tmp_path: Path) -> None:
        """The written record contains an `event_type` key equal to the class name."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        logger.handle(_started_event())

        record = _read_lines(log_file)[0]
        assert record["event_type"] == "WorkflowStarted"

    def test_model_fields_present(self, tmp_path: Path) -> None:
        """All model fields from WorkflowStarted are present in the written record."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        logger.handle(_started_event())

        record = _read_lines(log_file)[0]
        assert record["event_id"] == "evt-001"
        assert record["idea_title"] == "Test Idea"
        assert record["idea_slug"] == "test-idea"
        assert record["category"] == "cli_tool"
        assert "timestamp" in record

    def test_second_event_appends(self, tmp_path: Path) -> None:
        """A second handle() call appends a second line — does not truncate."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        logger.handle(_started_event())
        logger.handle(_completed_event())

        lines = _read_lines(log_file)
        assert len(lines) == 2
        assert lines[0]["event_type"] == "WorkflowStarted"
        assert lines[1]["event_type"] == "WorkflowCompleted"

    def test_completed_event_fields(self, tmp_path: Path) -> None:
        """WorkflowCompleted fields (repo_url, session_id, session_url) are written."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        logger.handle(_completed_event())

        record = _read_lines(log_file)[0]
        assert record["repo_url"] == "https://github.com/testuser/test-idea"
        assert record["session_id"] == "session-123"
        assert record["session_url"] == "https://jules.example.com/session/123"


# ---------------------------------------------------------------------------
# TestWriteFailure
# ---------------------------------------------------------------------------


class TestWriteFailure:
    def test_os_replace_failure_raises_audit_error(self, tmp_path: Path) -> None:
        """If the atomic rename fails, AuditError is raised (not a bare OSError)."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        with patch("src.services.audit.os.replace", side_effect=OSError("disk full")):
            with pytest.raises(AuditError, match="Failed to write audit log"):
                logger.handle(_started_event())

    def test_unexpected_error_raises_audit_error(self, tmp_path: Path) -> None:
        """Any unexpected exception during handle() is wrapped in AuditError."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        with patch("src.services.audit.os.write", side_effect=RuntimeError("boom")):
            with pytest.raises(AuditError):
                logger.handle(_started_event())


# ---------------------------------------------------------------------------
# TestNonDomainEventFiltering
# ---------------------------------------------------------------------------


class TestNonDomainEventFiltering:
    def test_non_domain_event_does_not_raise(self, tmp_path: Path) -> None:
        """Passing a plain object to handle() must not raise."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        # Should be silently ignored
        logger.handle("not-a-domain-event")

    def test_non_domain_event_does_not_create_file(self, tmp_path: Path) -> None:
        """Passing a non-DomainEvent must not create the log file."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        logger.handle({"some": "dict"})

        assert not log_file.exists()

    def test_none_does_not_raise(self, tmp_path: Path) -> None:
        """Passing None is silently ignored."""
        log_file = tmp_path / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(log_file))

        logger.handle(None)

        assert not log_file.exists()


# ---------------------------------------------------------------------------
# TestDirectoryCreation
# ---------------------------------------------------------------------------


class TestDirectoryCreation:
    def test_nested_directory_created_on_init(self, tmp_path: Path) -> None:
        """Logger creates parent directories that do not yet exist."""
        nested_log = tmp_path / "nested" / "deep" / "audit.jsonl"
        assert not nested_log.parent.exists()

        JsonFileAuditLogger(log_file=str(nested_log))

        assert nested_log.parent.exists()

    def test_existing_directory_does_not_raise(self, tmp_path: Path) -> None:
        """Init with an existing parent directory must not raise."""
        log_file = tmp_path / "audit.jsonl"
        JsonFileAuditLogger(log_file=str(log_file))  # should not raise

    def test_write_succeeds_after_nested_dir_creation(self, tmp_path: Path) -> None:
        """After creating nested dirs, a subsequent handle() writes successfully."""
        nested_log = tmp_path / "nested" / "audit.jsonl"
        logger = JsonFileAuditLogger(log_file=str(nested_log))

        logger.handle(_started_event())

        assert nested_log.exists()
        lines = _read_lines(nested_log)
        assert len(lines) == 1
        assert lines[0]["event_type"] == "WorkflowStarted"
