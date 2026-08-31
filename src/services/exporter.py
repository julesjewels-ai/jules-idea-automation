"""Data export services for Jules."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from src.core.interfaces import DataExporter, RecordProvider
from src.utils.errors import ExportError, ExportFormatError


class CSVExporter(DataExporter[dict[str, Any]]):
    """Exports records to CSV format."""

    def export(self, records: list[dict[str, Any]]) -> str:
        """Export records to a CSV string.

        Args:
        ----
            records: A list of dict records.

        Returns:
        -------
            A CSV-formatted string.

        """
        if not records:
            return ""

        output = io.StringIO()
        fieldnames = list(records[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        try:
            writer.writeheader()
            for record in records:
                # Ensure only the expected keys are written to avoid ValueError
                filtered_record = {k: record.get(k) for k in fieldnames}
                writer.writerow(filtered_record)
        except Exception as e:
            raise ExportError(f"Failed to generate CSV: {e}") from e

        return output.getvalue()


class JSONExporter(DataExporter[dict[str, Any]]):
    """Exports records to JSON format."""

    def export(self, records: list[dict[str, Any]]) -> str:
        """Export records to a JSON string.

        Args:
        ----
            records: A list of dict records.

        Returns:
        -------
            A JSON-formatted string.

        """
        try:
            return json.dumps(records, indent=2)
        except Exception as e:
            raise ExportError(f"Failed to generate JSON: {e}") from e

class ExporterFactory:
    """Factory for creating exporters based on format string."""

    @staticmethod
    def get_exporter(fmt: str) -> DataExporter[dict[str, Any]]:
        """Return the appropriate exporter for the given format.

        Args:
        ----
            fmt: The format string (e.g., 'csv', 'json').

        Returns:
        -------
            An instance of DataExporter.

        Raises:
        ------
            ExportFormatError: If the format is unknown.

        """
        fmt = fmt.lower()
        if fmt == "csv":
            return CSVExporter()
        if fmt == "json":
            return JSONExporter()

        raise ExportFormatError(
            f"Unsupported export format: {fmt}",
            tip="Supported formats are 'csv' and 'json'.",
        )


class ExportService:
    """Orchestrates fetching records and exporting them."""

    def __init__(
        self,
        provider: RecordProvider[dict[str, Any]],
        exporter: DataExporter[dict[str, Any]],
    ) -> None:
        """Initialize with a record provider and an exporter.

        Args:
        ----
            provider: Service that provides records.
            exporter: Service that formats the records.
        """
        self._provider = provider
        self._exporter = exporter

    def export(self, limit: int = 50) -> str:
        """Fetch records and return them as a formatted string.

        Args:
        ----
            limit: Maximum number of records to export.

        Returns:
        -------
            The formatted export string.

        Raises:
        ------
            ExportError: If fetching or exporting fails.

        """
        try:
            records = self._provider.list_records(limit=limit)
        except Exception as e:
            raise ExportError(f"Failed to fetch records: {e}") from e

        try:
            return self._exporter.export(records)
        except ExportError:
            raise
        except Exception as e:
            raise ExportError(f"Unexpected error during export: {e}") from e
