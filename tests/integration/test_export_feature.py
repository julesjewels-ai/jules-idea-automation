"""Integration tests for the Export feature."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from src.cli.cmd_export import handle_export
from src.services.db import HistoryDB


@pytest.fixture
def populated_db(tmp_path: Path) -> HistoryDB:
    """Create a temporary populated HistoryDB instance."""
    db = HistoryDB(db_path=tmp_path / "test_export_history.db")
    db.add_record(slug="test-app-1", repo_url="https://github.com/u/test-app-1")
    db.add_record(slug="test-app-2", repo_url="https://github.com/u/test-app-2", status="completed")
    return db


def test_export_csv_output(populated_db: HistoryDB, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that handle_export outputs valid CSV."""
    args = Namespace(command="export", format="csv", limit=50)

    with patch("src.cli.cmd_export.HistoryDB", return_value=populated_db):
        handle_export(args)

    captured = capsys.readouterr()
    output = captured.out

    assert "id,slug,repo_url,session_id,session_url,pr_url,status,created_at" in output
    assert "test-app-1" in output
    assert "test-app-2" in output


def test_export_json_output(populated_db: HistoryDB, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that handle_export outputs valid JSON."""
    args = Namespace(command="export", format="json", limit=50)

    with patch("src.cli.cmd_export.HistoryDB", return_value=populated_db):
        handle_export(args)

    captured = capsys.readouterr()
    output = captured.out

    # Output should be valid JSON
    data = json.loads(output)

    assert len(data) == 2
    assert data[0]["slug"] == "test-app-2"  # Newest first
    assert data[1]["slug"] == "test-app-1"


def test_export_no_records(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that handle_export correctly handles empty database."""
    args = Namespace(command="export", format="csv", limit=50)
    db = HistoryDB(db_path=tmp_path / "empty.db")

    with patch("src.cli.cmd_export.HistoryDB", return_value=db):
        handle_export(args)

    captured = capsys.readouterr()
    assert "No history records found." in captured.err
    assert captured.out == ""
