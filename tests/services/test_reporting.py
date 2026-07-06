"""Tests for the reporting service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.services.reporting import (
    AutomatedReportingService,
    FileReportStorage,
    MarkdownReportGenerator,
    ReportingError,
)


def test_reporting_service_integration(tmp_path: Path) -> None:
    """Test the end-to-end integration of the reporting service."""
    # Set up mock data
    mock_data = {
        "idea": {
            "title": "Test Project",
            "description": "A test project description.",
            "slug": "test-project",
            "tech_stack": ["Python", "Pytest"],
            "features": ["Feature A", "Feature B"],
        },
        "repo_url": "https://github.com/test/test-project",
        "session_id": "test-session-id",
        "session_url": "https://jules.google.com/test-session-id",
        "pr_url": "https://github.com/test/test-project/pull/1",
    }
    identifier = "test-project"

    # Instantiate concrete implementations
    generator = MarkdownReportGenerator()
    storage = FileReportStorage(output_dir=tmp_path)
    service = AutomatedReportingService(generator=generator, storage=storage)

    # Execute the service
    location = service.create_and_store_report(data=mock_data, identifier=identifier)

    # Verify output file
    output_file = Path(location)
    assert output_file.exists()
    assert output_file.name == f"{identifier}_report.md"

    # Verify content
    content = output_file.read_text(encoding="utf-8")
    assert "# Test Project" in content
    assert "**Slug**: test-project" in content
    assert "A test project description." in content
    assert "Python, Pytest" in content
    assert "- Feature A" in content
    assert "- Feature B" in content
    assert "[Link](https://github.com/test/test-project)" in content
    assert "test-session-id" in content
    assert "[Link](https://jules.google.com/test-session-id)" in content
    assert "[Link](https://github.com/test/test-project/pull/1)" in content


def test_markdown_generator_error_handling() -> None:
    """Test error handling in the Markdown generator."""
    generator = MarkdownReportGenerator()

    # We can pass bad data type (e.g. None instead of dict) to trigger exception
    with pytest.raises(ReportingError, match="Failed to generate Markdown report"):
        generator.generate(None)  # type: ignore[arg-type]


def test_file_storage_error_handling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test error handling in the file storage."""
    storage = FileReportStorage(output_dir=tmp_path)

    def mock_mkdir(*args: Any, **kwargs: Any) -> None:
        raise OSError("Mock permission error")

    monkeypatch.setattr(Path, "mkdir", mock_mkdir)

    with pytest.raises(ReportingError, match="Failed to save report to file"):
        storage.save("content", "test-id")
