"""Handler for the 'export' command."""

from __future__ import annotations

import sys
from argparse import Namespace

from src.core.interfaces import Exporter
from src.services.db import HistoryDB
from src.utils.errors import ExportError
from src.utils.exporter import HistoryExporter


def _do_export(db: HistoryDB, exporter: Exporter, fmt: str) -> None:
    """Perform the export using dependency injection."""
    # We assume export fetches all or a large number of records.
    # HistoryDB list_records has a limit, we can pass a large number like 1000.
    records = db.list_records(limit=1000)

    if not records:
        print("No history found. Run a workflow first to create entries.", file=sys.stderr)
        return

    # Call the exporter utility
    try:
        output = exporter.export(records, fmt=fmt)
        print(output, end="")
    except ExportError as e:
        print(f"Error exporting history: {e}", file=sys.stderr)
        sys.exit(1)


def handle_export_history(args: Namespace) -> None:
    """Export history records from the local database."""
    with HistoryDB() as db:
        exporter = HistoryExporter()
        _do_export(db, exporter, args.format)
