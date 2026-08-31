"""Integration tests for the CLI export command."""

from __future__ import annotations

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from src.cli.cmd_export import handle_export


def test_handle_export_success_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test handle_export outputs JSON correctly to stdout."""
    # Given
    mock_records = [{"id": 1, "slug": "test-repo"}]
    mock_db = MagicMock()
    mock_db.list_records.return_value = mock_records

    args = Namespace(format="json", limit=10)

    # When
    with patch("src.cli.cmd_export.HistoryDB", return_value=mock_db):
        mock_db.__enter__.return_value = mock_db
        handle_export(args)

    # Then
    captured = capsys.readouterr()
    output = captured.out.strip()

    # Output should be valid JSON matching mock records
    parsed = json.loads(output)
    assert parsed == mock_records


def test_handle_export_no_history(capsys: pytest.CaptureFixture[str]) -> None:
    """Test handle_export outputs appropriate message when history is empty."""
    # Given
    mock_db = MagicMock()
    mock_db.list_records.return_value = []

    args = Namespace(format="csv", limit=100)

    # When
    with patch("src.cli.cmd_export.HistoryDB", return_value=mock_db):
        mock_db.__enter__.return_value = mock_db
        handle_export(args)

    # Then
    captured = capsys.readouterr()
    assert "No history found to export" in captured.err


def test_handle_export_db_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Test handle_export safely exits on export error."""
    # Given
    mock_db = MagicMock()
    mock_db.list_records.side_effect = Exception("DB Error")

    args = Namespace(format="csv", limit=50)

    # When
    with patch("src.cli.cmd_export.HistoryDB", return_value=mock_db):
        mock_db.__enter__.return_value = mock_db
        try:
            handle_export(args)
        except SystemExit as e:
            assert e.code == 1

    # Then
    captured = capsys.readouterr()
    assert "Export failed: Failed to fetch records: DB Error" in captured.err
