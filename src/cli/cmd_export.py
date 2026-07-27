"""Handler for the 'export' command."""

from __future__ import annotations

import sys
from argparse import Namespace

from src.services.db import HistoryDB
from src.services.exporter import ExporterFactory
from src.utils.errors import ExportError


def handle_export(args: Namespace) -> None:
    """Handle the export command."""
    format_type = getattr(args, "format", "csv")

    try:
        exporter = ExporterFactory.create(format_type)
    except ExportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with HistoryDB() as db:
        records = db.list_records()

    if not records:
        print("No history found to export.", file=sys.stderr)
        return

    try:
        output = exporter.export(records)
        print(output, end="")
    except ExportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
