"""Tests for the FileCacheProvider service."""

import hashlib
import json
import pytest
from src.services.cache import FileCacheProvider


@pytest.fixture
def cache_dir(tmp_path):
    """Fixture for a temporary cache directory."""
    return tmp_path / "cache"


@pytest.fixture
def cache_provider(cache_dir):
    """Fixture for FileCacheProvider."""
    return FileCacheProvider(cache_dir=str(cache_dir))


def test_init_creates_directory(cache_dir):
    """Test that the cache directory is created on initialization."""
    FileCacheProvider(cache_dir=str(cache_dir))
    assert cache_dir.exists()


def test_set_and_get(cache_provider):
    """Test setting and getting a value."""
    key = "test_key"
    value = {"data": "test_value"}

    cache_provider.set(key, value)
    result = cache_provider.get(key)

    assert result == value


def test_get_non_existent(cache_provider):
    """Test getting a non-existent key."""
    result = cache_provider.get("non_existent")
    assert result is None


def test_delete(cache_provider):
    """Test deleting a key."""
    key = "test_key"
    value = {"data": "test_value"}

    cache_provider.set(key, value)
    assert cache_provider.get(key) is not None

    cache_provider.delete(key)
    assert cache_provider.get(key) is None


def test_delete_non_existent(cache_provider):
    """Test deleting a non-existent key (should not raise error)."""
    cache_provider.delete("non_existent")


def test_file_integrity(cache_provider, cache_dir):
    """Test that files are written correctly."""
    key = "test_key"
    value = {"data": "test_value"}

    cache_provider.set(key, value)

    # Manually check the file
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    file_path = cache_dir / f"{hashed_key}.json"

    assert file_path.exists()
    with open(file_path, "r") as f:
        content = json.load(f)
    assert content == value


def test_read_error_returns_none(cache_provider, cache_dir):
    """Test that reading a corrupted file returns None."""
    key = "test_key"

    # Create a corrupted file
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    file_path = cache_dir / f"{hashed_key}.json"

    with open(file_path, "w") as f:
        f.write("invalid json")

    result = cache_provider.get(key)
    assert result is None
