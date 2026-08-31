"""Tests for the exporter services."""

from __future__ import annotations

import json
from typing import Any

import pytest

from src.core.interfaces import RecordProvider
from src.services.exporter import CSVExporter, ExporterFactory, ExportService, JSONExporter
from src.utils.errors import ExportError, ExportFormatError


class MockRecordProvider(RecordProvider[dict[str, Any]]):
    """Mock record provider for testing."""

    def __init__(self, records: list[dict[str, Any]] | None = None, should_fail: bool = False):
        self._records = records or []
        self._should_fail = should_fail

    def list_records(self, limit: int = 50) -> list[dict[str, Any]]:
        if self._should_fail:
            raise RuntimeError("Database error")
        return self._records[:limit]


def test_csv_exporter() -> None:
    """Test CSVExporter generates correct CSV strings."""
    exporter = CSVExporter()
    records = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    output = exporter.export(records)

    # Assert header and data rows
    assert "id,name\r\n" in output
    assert "1,Alice\r\n" in output
    assert "2,Bob\r\n" in output


def test_csv_exporter_empty() -> None:
    """Test CSVExporter handles empty records correctly."""
    exporter = CSVExporter()
    output = exporter.export([])
    assert output == ""


def test_json_exporter() -> None:
    """Test JSONExporter generates correct JSON strings."""
    exporter = JSONExporter()
    records = [{"id": 1, "name": "Alice"}]

    output = exporter.export(records)

    # Assert output is valid JSON and matches expected
    parsed = json.loads(output)
    assert len(parsed) == 1
    assert parsed[0]["id"] == 1
    assert parsed[0]["name"] == "Alice"


def test_exporter_factory() -> None:
    """Test ExporterFactory creates correct instances and handles errors."""
    csv_exp = ExporterFactory.get_exporter("csv")
    assert isinstance(csv_exp, CSVExporter)

    json_exp = ExporterFactory.get_exporter("json")
    assert isinstance(json_exp, JSONExporter)

    # Case insensitivity
    assert isinstance(ExporterFactory.get_exporter("CSV"), CSVExporter)

    with pytest.raises(ExportFormatError, match="Unsupported export format: xml"):
        ExporterFactory.get_exporter("xml")


def test_export_service() -> None:
    """Test ExportService orchestration from provider to exporter."""
    records = [{"id": 1, "status": "active"}]
    provider = MockRecordProvider(records)
    exporter = JSONExporter()

    service = ExportService(provider=provider, exporter=exporter)
    output = service.export()

    parsed = json.loads(output)
    assert parsed == records


def test_export_service_provider_error() -> None:
    """Test ExportService handles provider errors correctly."""
    provider = MockRecordProvider(should_fail=True)
    exporter = CSVExporter()

    service = ExportService(provider=provider, exporter=exporter)

    with pytest.raises(ExportError, match="Failed to fetch records: Database error"):
        service.export()


def test_export_service_limit() -> None:
    """Test ExportService passes the correct limit to the provider."""
    records = [
        {"id": 1},
        {"id": 2},
        {"id": 3},
        {"id": 4},
        {"id": 5},
    ]
    provider = MockRecordProvider(records)
    exporter = JSONExporter()
    service = ExportService(provider=provider, exporter=exporter)

    output = service.export(limit=2)
    parsed = json.loads(output)

    assert len(parsed) == 2
    assert parsed == [{"id": 1}, {"id": 2}]
