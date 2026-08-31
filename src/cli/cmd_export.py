"""Handler for the 'export' command."""

from __future__ import annotations

import sys
from argparse import Namespace

from src.services.db import HistoryDB
from src.services.exporter import ExporterFactory, ExportService
from src.utils.errors import ExportError


def handle_export(args: Namespace) -> None:
    """Export the local history database to the requested format."""
    fmt = getattr(args, "format", "csv")
    limit = getattr(args, "limit", 1000)

    try:
        exporter = ExporterFactory.get_exporter(fmt)
        with HistoryDB() as db:
            service = ExportService(provider=db, exporter=exporter)
            output = service.export(limit=limit)

        if output:
            print(output)
        else:
            print("No history found to export.", file=sys.stderr)

    except ExportError as e:
        print(f"Export failed: {e}", file=sys.stderr)
        sys.exit(1)
