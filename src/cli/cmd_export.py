"""Handler for the 'export' command."""

from __future__ import annotations

import sys
from argparse import Namespace

from src.services.db import HistoryDB
from src.utils.exporter import CsvExporter, ExportService, JsonExporter


def handle_export(args: Namespace) -> None:
    """Handle the export command to retrieve and format history records.

    Args:
    ----
        args: The parsed command-line arguments.

    """
    if getattr(args, "format", "csv") == "json":
        exporter = JsonExporter()
    else:
        exporter = CsvExporter()  # type: ignore[assignment]

    with HistoryDB() as db:
        service = ExportService(repository=db, exporter=exporter)
        result = service.export_history(limit=getattr(args, "limit", 50))

    if result:
        print(result.rstrip())
    else:
        print("No history records found.", file=sys.stderr)
