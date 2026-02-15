"""Tests for file cache provider."""

import shutil
import tempfile

import pytest

from src.services.cache import FileCacheProvider
from src.utils.errors import CacheError


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_cache_set_and_get(temp_cache_dir):
    """Test setting and getting a value from cache."""
    cache = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "test_key"
    value = {"data": "test_value"}

    cache.set(key, value)
    cached_value = cache.get(key)

    assert cached_value == value


def test_cache_miss(temp_cache_dir):
    """Test getting a non-existent key."""
    cache = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "non_existent_key"

    cached_value = cache.get(key)

    assert cached_value is None


def test_cache_persistence(temp_cache_dir):
    """Test that cache persists across instances."""
    cache1 = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "persistent_key"
    value = {"data": 123}
    cache1.set(key, value)

    cache2 = FileCacheProvider(cache_dir=temp_cache_dir)
    cached_value = cache2.get(key)

    assert cached_value == value


def test_cache_directory_creation_failure():
    """Test error handling when cache directory cannot be created."""
    # Try to create cache in a read-only directory or invalid path
    # Using a file path as dir should raise OSError
    with tempfile.NamedTemporaryFile() as f:
        # Pass the file path as the directory.
        with pytest.raises(CacheError):
            FileCacheProvider(cache_dir=f.name)
