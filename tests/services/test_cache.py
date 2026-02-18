"""Tests for the FileCacheProvider service."""

import os
import time
import pytest
import shutil
from src.services.cache import FileCacheProvider


from typing import Generator
from pathlib import Path


@pytest.fixture
def cache_dir(tmp_path: Path) -> Generator[str, None, None]:
    """Fixture to provide a temporary cache directory."""
    path = tmp_path / "cache"
    yield str(path)
    # Cleanup if needed, though tmp_path is auto-cleaned by pytest
    if os.path.exists(path):
        shutil.rmtree(path)


def test_cache_set_and_get(cache_dir: str) -> None:
    """Test setting and getting a value."""
    cache = FileCacheProvider(cache_dir=cache_dir)
    key = "test_key"
    value = {"foo": "bar"}

    cache.set(key, value)
    cached_value = cache.get(key)

    assert cached_value == value


def test_cache_miss(cache_dir: str) -> None:
    """Test getting a non-existent key."""
    cache = FileCacheProvider(cache_dir=cache_dir)
    assert cache.get("missing_key") is None


def test_cache_delete(cache_dir: str) -> None:
    """Test deleting a value."""
    cache = FileCacheProvider(cache_dir=cache_dir)
    key = "test_key"
    value = "some_value"

    cache.set(key, value)
    assert cache.get(key) == value

    cache.delete(key)
    assert cache.get(key) is None


def test_cache_ttl_expired(cache_dir: str) -> None:
    """Test TTL expiration."""
    cache = FileCacheProvider(cache_dir=cache_dir)
    key = "ttl_key"
    value = "ttl_value"

    # Set with 0.1 second TTL
    cache.set(key, value, ttl=0.1)

    # Should be there immediately
    assert cache.get(key) == value

    # Wait for expiration
    time.sleep(0.2)

    # Should be gone
    assert cache.get(key) is None


def test_cache_persistence(cache_dir: str) -> None:
    """Test that cache persists across instances."""
    cache1 = FileCacheProvider(cache_dir=cache_dir)
    key = "persist_key"
    value = "persist_value"

    cache1.set(key, value)

    # New instance pointing to same dir
    cache2 = FileCacheProvider(cache_dir=cache_dir)
    assert cache2.get(key) == value
