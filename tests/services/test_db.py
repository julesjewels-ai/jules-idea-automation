"""Tests for src.services.db.HistoryDB."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.db import HistoryDB


@pytest.fixture
def db(tmp_path: Path) -> HistoryDB:
    """Create a temporary HistoryDB instance."""
    return HistoryDB(db_path=tmp_path / "test_history.db")


class TestAddRecord:
    """Tests for HistoryDB.add_record()."""

    def test_returns_positive_id(self, db: HistoryDB) -> None:
        row_id = db.add_record(slug="my-app", repo_url="https://github.com/u/my-app")
        assert row_id >= 1

    def test_successive_ids_increment(self, db: HistoryDB) -> None:
        id1 = db.add_record(slug="a", repo_url="https://github.com/u/a")
        id2 = db.add_record(slug="b", repo_url="https://github.com/u/b")
        assert id2 > id1


class TestListRecords:
    """Tests for HistoryDB.list_records()."""

    def test_empty_db_returns_empty_list(self, db: HistoryDB) -> None:
        assert db.list_records() == []

    def test_records_are_newest_first(self, db: HistoryDB) -> None:
        db.add_record(slug="first", repo_url="https://github.com/u/first")
        db.add_record(slug="second", repo_url="https://github.com/u/second")
        records = db.list_records()
        assert records[0]["slug"] == "second"
        assert records[1]["slug"] == "first"

    def test_limit_parameter(self, db: HistoryDB) -> None:
        for i in range(5):
            db.add_record(slug=f"app-{i}", repo_url=f"https://github.com/u/app-{i}")
        assert len(db.list_records(limit=3)) == 3

    def test_record_contains_expected_keys(self, db: HistoryDB) -> None:
        db.add_record(
            slug="test",
            repo_url="https://github.com/u/test",
            session_id="sid-123",
            session_url="https://jules.google.com/s/sid-123",
        )
        rec = db.list_records()[0]
        assert rec["slug"] == "test"
        assert rec["repo_url"] == "https://github.com/u/test"
        assert rec["session_id"] == "sid-123"
        assert rec["status"] == "created"
        assert rec["created_at"] is not None


class TestUpdateRecord:
    """Tests for HistoryDB.update_record()."""

    def test_update_status(self, db: HistoryDB) -> None:
        row_id = db.add_record(slug="x", repo_url="https://github.com/u/x")
        db.update_record(row_id, status="completed")
        rec = db.list_records()[0]
        assert rec["status"] == "completed"

    def test_update_pr_url(self, db: HistoryDB) -> None:
        row_id = db.add_record(slug="x", repo_url="https://github.com/u/x")
        db.update_record(row_id, pr_url="https://github.com/u/x/pull/1")
        rec = db.list_records()[0]
        assert rec["pr_url"] == "https://github.com/u/x/pull/1"

    def test_ignores_disallowed_fields(self, db: HistoryDB) -> None:
        row_id = db.add_record(slug="x", repo_url="https://github.com/u/x")
        # 'slug' is not in the allowed update set; should be silently ignored
        db.update_record(row_id, slug="hacked")
        rec = db.list_records()[0]
        assert rec["slug"] == "x"
