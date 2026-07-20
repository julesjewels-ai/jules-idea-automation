from __future__ import annotations

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

from src.cli.cmd_export import _do_export, handle_export_history
from src.utils.errors import ExportError


def test_handle_export_no_records(capsys):
    """Test export when no records exist."""
    args = Namespace(format="csv")
    with patch("src.cli.cmd_export.HistoryDB") as mock_db:
        mock_db.return_value.__enter__.return_value.list_records.return_value = []
        handle_export_history(args)

    captured = capsys.readouterr()
    assert "No history found" in captured.err


def test_handle_export_csv(capsys):
    """Test exporting records to CSV format."""
    args = Namespace(format="csv")
    records = [{"id": 1, "slug": "test-slug"}]

    with patch("src.cli.cmd_export.HistoryDB") as mock_db:
        mock_db.return_value.__enter__.return_value.list_records.return_value = records
        handle_export_history(args)

    captured = capsys.readouterr()
    assert "id,slug" in captured.out
    assert "1,test-slug" in captured.out


def test_handle_export_json(capsys):
    """Test exporting records to JSON format."""
    args = Namespace(format="json")
    records = [{"id": 1, "slug": "test-slug"}]

    with patch("src.cli.cmd_export.HistoryDB") as mock_db:
        mock_db.return_value.__enter__.return_value.list_records.return_value = records
        handle_export_history(args)

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["slug"] == "test-slug"


def test_do_export_error(capsys):
    """Test export handling errors gracefully."""
    db = MagicMock()
    db.list_records.return_value = [{"id": 1}]

    exporter = MagicMock()
    exporter.export.side_effect = ExportError("Invalid format")

    try:
        _do_export(db, exporter, "unknown")
    except SystemExit:
        pass

    captured = capsys.readouterr()
    assert "Error exporting history:" in captured.err
