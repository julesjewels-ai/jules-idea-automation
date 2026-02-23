"""Tests for FileCacheProvider."""
import json
import hashlib
from pathlib import Path
from src.services.cache import FileCacheProvider


def test_file_cache_set_and_get(tmp_path: Path) -> None:
    """Test setting and getting values from the cache."""
    cache = FileCacheProvider(cache_dir=str(tmp_path))
    key = "test_key"
    value = {"data": "test_data"}

    cache.set(key, value)
    retrieved = cache.get(key)

    assert retrieved == value

    # Verify file existence and content
    hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
    cache_file = tmp_path / f"{hashed_key}.json"
    assert cache_file.exists()

    with open(cache_file, "r") as f:
        content = json.load(f)
    assert content == value


def test_file_cache_delete(tmp_path: Path) -> None:
    """Test deleting values from the cache."""
    cache = FileCacheProvider(cache_dir=str(tmp_path))
    key = "test_key"
    value = {"data": "test_data"}

    cache.set(key, value)
    assert cache.get(key) == value

    cache.delete(key)
    assert cache.get(key) is None

    hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
    cache_file = tmp_path / f"{hashed_key}.json"
    assert not cache_file.exists()


def test_file_cache_miss(tmp_path: Path) -> None:
    """Test cache miss returns None."""
    cache = FileCacheProvider(cache_dir=str(tmp_path))
    assert cache.get("non_existent_key") is None
