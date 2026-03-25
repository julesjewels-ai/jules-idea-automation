"""Root conftest.py — project-wide pytest configuration."""

from __future__ import annotations

from pathlib import Path


def pytest_ignore_collect(collection_path: Path, config: object) -> bool | None:  # noqa: ARG001
    """Skip files that cannot be stat()'d due to macOS permission restrictions.

    Some root-level files (.DS_Store, .coverage, .env, etc.) are not
    readable in this environment and cause pytest to abort with a PermissionError
    before collection starts. Returning True tells pytest to silently ignore them.
    """
    try:
        collection_path.stat()
        return None  # Let pytest decide
    except PermissionError:
        return True  # Skip this path

