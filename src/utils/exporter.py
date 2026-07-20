from __future__ import annotations

import csv
import io
import json
from typing import Any

from src.core.interfaces import Exporter
from src.utils.errors import ExportError


class HistoryExporter(Exporter):
    """Utility class to export history records to different formats."""

    def export(self, records: list[dict[str, Any]], fmt: str = "csv") -> str:
        """Export a list of records to the specified format.

        Args:
        ----
            records: List of dictionaries representing history records.
            fmt: The format to export to (either "csv" or "json").

        Returns:
        -------
            A string containing the exported data.

        Raises:
        ------
            ExportError: If the export fails or format is unsupported.

        """
        if not records:
            return ""

        try:
            if fmt == "json":
                return json.dumps(records, indent=2)
            elif fmt == "csv":
                output = io.StringIO()
                # Ensure consistent column ordering by taking keys from the first record,
                # assuming all records share the same schema from SQLite.
                fieldnames = list(records[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
                return output.getvalue()
            else:
                raise ExportError(f"Unsupported export format: {fmt}", tip="Use 'csv' or 'json'.")
        except Exception as e:
            if isinstance(e, ExportError):
                raise
            raise ExportError(f"Failed to export data: {e}") from e
