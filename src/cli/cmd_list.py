"""Handler for the 'list' command."""

from __future__ import annotations

import sys
from argparse import Namespace
from datetime import datetime, timezone

from src.services.db import HistoryDB


def handle_list_history(args: Namespace) -> None:
    """Display past generated projects from the local history database."""
    with HistoryDB() as db:
        records = db.list_records()

    if not records:
        print("No history found. Run a workflow first to create entries.")
        return

    # Column definitions: (header, key, width)
    columns = [
        ("ID", "id", 4),
        ("Slug", "slug", 30),
        ("Status", "status", 10),
        ("Session ID", "session_id", 20),
        ("Created", "created_at", 20),
    ]

    header = "  ".join(h.ljust(w) for h, _, w in columns)
    separator = "  ".join("-" * w for _, _, w in columns)

    print(header)
    print(separator)

    for rec in records:
        parts: list[str] = []
        for _, key, width in columns:
            value = rec.get(key)
            if key == "created_at" and value is not None:
                value = datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            parts.append(str(value or "—").ljust(width))
        print("  ".join(parts))

    print(f"\n{len(records)} record(s) total.", file=sys.stderr)
