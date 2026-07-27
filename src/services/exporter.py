"""Exporter service implementations."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from src.core.interfaces import Exporter
from src.utils.errors import ExportError


class CsvExporter(Exporter):
    """Exporter that formats data as CSV."""

    def export(self, data: list[dict[str, Any]]) -> str:
        """Export data to CSV format.

        Args:
        ----
            data: The list of dictionaries to export.

        Returns:
        -------
            The data formatted as a CSV string.

        Raises:
        ------
            ExportError: If data conversion fails.

        """
        if not data:
            return ""

        try:
            output = io.StringIO()
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
            return output.getvalue()
        except Exception as e:
            raise ExportError(f"Failed to export data to CSV: {e}") from e


class JsonExporter(Exporter):
    """Exporter that formats data as JSON."""

    def export(self, data: list[dict[str, Any]]) -> str:
        """Export data to JSON format.

        Args:
        ----
            data: The list of dictionaries to export.

        Returns:
        -------
            The data formatted as a JSON string.

        Raises:
        ------
            ExportError: If data conversion fails.

        """
        try:
            return json.dumps(data, indent=2)
        except Exception as e:
            raise ExportError(f"Failed to export data to JSON: {e}") from e


class ExporterFactory:
    """Factory for creating Exporter instances."""

    @staticmethod
    def create(format_type: str) -> Exporter:
        """Create an exporter of the given type.

        Args:
        ----
            format_type: The type of exporter to create ('csv' or 'json').

        Returns:
        -------
            An instance of the requested exporter.

        Raises:
        ------
            ExportError: If the format type is unsupported.

        """
        if format_type.lower() == "csv":
            return CsvExporter()
        elif format_type.lower() == "json":
            return JsonExporter()
        else:
            raise ExportError(f"Unsupported export format: {format_type}")
