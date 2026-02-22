"""Tests for the FileCacheProvider."""

import json
import time
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from src.services.cache import FileCacheProvider


@pytest.fixture  # type: ignore
def cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory."""
    return tmp_path / "cache"


@pytest.fixture  # type: ignore
def provider(cache_dir: Path) -> FileCacheProvider:
    """Create a FileCacheProvider instance."""
    return FileCacheProvider(cache_dir=str(cache_dir))


def test_init_creates_directory(cache_dir: Path) -> None:
    """Test that the cache directory is created on initialization."""
    assert not cache_dir.exists()
    FileCacheProvider(cache_dir=str(cache_dir))
    assert cache_dir.exists()


def test_set_and_get(provider: FileCacheProvider, cache_dir: Path) -> None:
    """Test basic set and get operations."""
    key = "test_key"
    value = {"foo": "bar"}

    provider.set(key, value)
    cached_value = provider.get(key)

    assert cached_value == value

    # Verify file existence and content
    hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{hashed_key}.json"
    assert cache_file.exists()

    with open(cache_file, "r") as f:
        data = json.load(f)
        assert data["value"] == value


def test_get_miss(provider: FileCacheProvider) -> None:
    """Test cache miss returns None."""
    assert provider.get("non_existent_key") is None


def test_delete(provider: FileCacheProvider) -> None:
    """Test deleting a cached item."""
    key = "test_key"
    value = "test_value"

    provider.set(key, value)
    assert provider.get(key) == value

    provider.delete(key)
    assert provider.get(key) is None


def test_ttl_expiry(provider: FileCacheProvider) -> None:
    """Test that expired items are not returned."""
    key = "expired_key"
    value = "expired_value"

    # Set with 0.1s TTL
    provider.set(key, value, ttl=0.1)

    # Should be available immediately
    assert provider.get(key) == value

    # Wait for expiry
    time.sleep(0.2)
    assert provider.get(key) is None


def test_corrupt_cache_file(
        provider: FileCacheProvider, cache_dir: Path) -> None:
    """Test handling of corrupt cache files."""
    key = "corrupt_key"
    hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{hashed_key}.json"

    # Create invalid JSON file
    with open(cache_file, "w") as f:
        f.write("{invalid_json")

    assert provider.get(key) is None


def test_cache_init_failure_handled(tmp_path: Path) -> None:
    """Test that init failure (e.g. permissions) is handled gracefully."""
    # This is hard to simulate perfectly without mocking Path.mkdir or similar,
    # but we can try to point to a file as a directory
    file_path = tmp_path / "file"
    file_path.touch()

    # Should log warning but not crash
    with patch("src.services.cache.logger") as mock_logger:
        FileCacheProvider(cache_dir=str(file_path))

        # Verify warning logged
        mock_logger.warning.assert_called()
