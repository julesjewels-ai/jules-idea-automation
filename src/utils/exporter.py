"""Service for exporting historical data."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from src.core.interfaces import DataExporter, HistoryRepository
from src.utils.errors import ExportError


class CsvExporter(DataExporter):
    """Exports data to a CSV format string."""

    def export(self, data: list[dict[str, Any]]) -> str:
        """Export the provided data to CSV string representation.

        Args:
        ----
            data: The list of records to export.

        Returns:
        -------
            The formatted string representation of the data in CSV format.

        Raises:
        ------
            ExportError: If data conversion fails.

        """
        if not data:
            return ""

        try:
            output = io.StringIO()
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)

            writer.writeheader()
            for row in data:
                writer.writerow(row)

            return output.getvalue()
        except Exception as e:
            raise ExportError(f"Failed to export data to CSV: {e}") from e


class JsonExporter(DataExporter):
    """Exports data to a JSON format string."""

    def export(self, data: list[dict[str, Any]]) -> str:
        """Export the provided data to JSON string representation.

        Args:
        ----
            data: The list of records to export.

        Returns:
        -------
            The formatted string representation of the data in JSON format.

        Raises:
        ------
            ExportError: If data conversion fails.

        """
        try:
            return json.dumps(data, indent=2)
        except (TypeError, ValueError) as e:
            raise ExportError(f"Failed to export data to JSON: {e}") from e


class ExportService:
    """Service to handle orchestration of exporting data."""

    def __init__(self, repository: HistoryRepository, exporter: DataExporter) -> None:
        """Initialize ExportService with dependencies.

        Args:
        ----
            repository: Service providing access to historical data.
            exporter: Service providing specific formatting logic.

        """
        self._repository = repository
        self._exporter = exporter

    def export_history(self, limit: int = 50) -> str:
        """Fetch history and export it using the injected exporter.

        Args:
        ----
            limit: Maximum number of records to retrieve for export.

        Returns:
        -------
            The formatted output string containing exported data.

        """
        data = self._repository.list_records(limit=limit)
        return self._exporter.export(data)
