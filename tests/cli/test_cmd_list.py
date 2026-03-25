"""Tests for the CLI 'list' command handler."""

from __future__ import annotations

import time
from argparse import Namespace
from pathlib import Path

import pytest

from src.cli.cmd_list import handle_list_history
from src.services.db import HistoryDB


@pytest.fixture
def populated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> HistoryDB:
    """Create a temp HistoryDB and monkeypatch cmd_list to use it."""
    db = HistoryDB(db_path=tmp_path / "test.db")
    db.add_record(slug="alpha", repo_url="https://github.com/u/alpha", session_id="s1")
    db.add_record(slug="beta", repo_url="https://github.com/u/beta")

    # Patch HistoryDB constructor inside cmd_list to return our test db
    monkeypatch.setattr("src.cli.cmd_list.HistoryDB", lambda: db)
    return db


def test_list_prints_records(populated_db: HistoryDB, capsys: pytest.CaptureFixture[str]) -> None:
    handle_list_history(Namespace())
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_list_empty_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    db = HistoryDB(db_path=tmp_path / "empty.db")
    monkeypatch.setattr("src.cli.cmd_list.HistoryDB", lambda: db)

    handle_list_history(Namespace())
    out = capsys.readouterr().out
    assert "No history found" in out
