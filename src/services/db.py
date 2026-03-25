"""SQLite-backed history database for tracking generated projects."""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB_DIR = Path.home() / ".jules"
_DEFAULT_DB_NAME = "history.db"

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT    NOT NULL,
    repo_url    TEXT    NOT NULL,
    session_id  TEXT,
    session_url TEXT,
    pr_url      TEXT,
    status      TEXT    NOT NULL DEFAULT 'created',
    created_at  REAL    NOT NULL
);
"""


class HistoryDB:
    """Thin wrapper around a local SQLite database for run history.

    The database is stored at ``~/.jules/history.db`` by default but the
    path can be overridden for testing.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            _DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
            db_path = _DEFAULT_DB_DIR / _DEFAULT_DB_NAME

        self._db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._conn.commit()
        logger.debug("History DB initialised at %s", self._db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_record(
        self,
        slug: str,
        repo_url: str,
        session_id: str | None = None,
        session_url: str | None = None,
        pr_url: str | None = None,
        status: str = "created",
    ) -> int:
        """Insert a new history record and return its ``id``."""
        cur = self._conn.execute(
            "INSERT INTO history (slug, repo_url, session_id, session_url, pr_url, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (slug, repo_url, session_id, session_url, pr_url, status, time.time()),
        )
        self._conn.commit()
        row_id: int = cur.lastrowid  # type: ignore[assignment]
        logger.debug("Inserted history record id=%d for slug=%s", row_id, slug)
        return row_id

    def list_records(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent *limit* history records (newest first)."""
        rows = self._conn.execute(
            "SELECT * FROM history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def update_record(self, record_id: int, **fields: Any) -> None:
        """Update one or more columns on the record identified by *record_id*."""
        allowed = {"session_id", "session_url", "pr_url", "status"}
        to_set = {k: v for k, v in fields.items() if k in allowed}
        if not to_set:
            return

        set_clause = ", ".join(f"{col} = ?" for col in to_set)
        values = list(to_set.values()) + [record_id]
        self._conn.execute(
            f"UPDATE history SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        self._conn.commit()
        logger.debug("Updated history record id=%d: %s", record_id, to_set)

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    def __enter__(self) -> HistoryDB:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
