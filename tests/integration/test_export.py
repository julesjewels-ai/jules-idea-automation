"""Integration tests for the export command."""

from __future__ import annotations

import json
from argparse import Namespace
from unittest.mock import patch

from src.cli.cmd_export import handle_export


def test_handle_export_csv(capsys):
    """Test exporting history to CSV format."""
    mock_records = [
        {"id": 1, "slug": "test-repo-1", "status": "completed"},
        {"id": 2, "slug": "test-repo-2", "status": "failed"},
    ]

    with patch("src.cli.cmd_export.HistoryDB") as MockDB:
        mock_db_instance = MockDB.return_value.__enter__.return_value
        mock_db_instance.list_records.return_value = mock_records

        args = Namespace(format="csv")
        handle_export(args)

    captured = capsys.readouterr()
    output = captured.out

    assert "id,slug,status" in output
    assert "1,test-repo-1,completed" in output
    assert "2,test-repo-2,failed" in output


def test_handle_export_json(capsys):
    """Test exporting history to JSON format."""
    mock_records = [
        {"id": 1, "slug": "test-repo-1", "status": "completed"},
        {"id": 2, "slug": "test-repo-2", "status": "failed"},
    ]

    with patch("src.cli.cmd_export.HistoryDB") as MockDB:
        mock_db_instance = MockDB.return_value.__enter__.return_value
        mock_db_instance.list_records.return_value = mock_records

        args = Namespace(format="json")
        handle_export(args)

    captured = capsys.readouterr()
    output = captured.out

    parsed_output = json.loads(output)
    assert len(parsed_output) == 2
    assert parsed_output[0]["id"] == 1
    assert parsed_output[0]["slug"] == "test-repo-1"
    assert parsed_output[1]["status"] == "failed"
