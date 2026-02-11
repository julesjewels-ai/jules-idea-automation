"""Tests for the FileCacheProvider service."""

import json
import os
import shutil
import tempfile
from typing import Generator

import pytest
from src.services.cache import FileCacheProvider
from src.utils.errors import CacheError


@pytest.fixture
def temp_cache_dir() -> Generator[str, None, None]:
    """Fixture to provide a temporary directory for cache."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_init_creates_directory(temp_cache_dir: str) -> None:
    """Test that initialization creates the cache directory."""
    cache_path = os.path.join(temp_cache_dir, "test_cache")
    FileCacheProvider(cache_dir=cache_path)
    assert os.path.exists(cache_path)


def test_init_raises_error_on_failure() -> None:
    """Test that initialization raises CacheError on failure."""
    # Try to create cache in a read-only directory or invalid path
    # Using an empty string usually raises OSError or similar depending on OS,
    # but for consistent testing we might mock os.makedirs.
    # Here we'll try to use a file as a directory.
    with tempfile.NamedTemporaryFile() as f:
        with pytest.raises(CacheError):
            FileCacheProvider(cache_dir=f.name)


def test_set_and_get_success(temp_cache_dir: str) -> None:
    """Test setting and getting a value."""
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "test_key"
    value = {"foo": "bar", "baz": 123}

    provider.set(key, value)
    retrieved = provider.get(key)

    assert retrieved == value


def test_get_nonexistent_key(temp_cache_dir: str) -> None:
    """Test getting a key that doesn't exist."""
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    assert provider.get("nonexistent") is None


def test_get_invalid_json(temp_cache_dir: str) -> None:
    """Test getting a key associated with a corrupted file."""
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "corrupt"
    path = provider._get_path(key)

    # Write invalid JSON
    with open(path, 'w') as f:
        f.write("{invalid_json")

    assert provider.get(key) is None
