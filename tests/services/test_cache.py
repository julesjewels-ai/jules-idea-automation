import os
import shutil
import tempfile
import pytest
from typing import Generator
from src.services.cache import FileCacheProvider

@pytest.fixture  # type: ignore[untyped-decorator]
def temp_cache_dir() -> Generator[str, None, None]:
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_file_cache_provider_set_get(temp_cache_dir: str) -> None:
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "test_key"
    value = {"data": "test_value"}

    provider.set(key, value)
    cached = provider.get(key)

    assert cached == value

def test_file_cache_provider_get_miss(temp_cache_dir: str) -> None:
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    cached = provider.get("non_existent_key")
    assert cached is None

def test_file_cache_provider_delete(temp_cache_dir: str) -> None:
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "test_key_delete"
    value = "data"

    provider.set(key, value)
    assert provider.get(key) == value

    provider.delete(key)
    assert provider.get(key) is None

def test_file_cache_provider_persistence(temp_cache_dir: str) -> None:
    provider1 = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "persist_key"
    value = "persist_value"

    provider1.set(key, value)

    provider2 = FileCacheProvider(cache_dir=temp_cache_dir)
    assert provider2.get(key) == value
