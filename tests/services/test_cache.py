"""Tests for the caching service."""

import json
import shutil
import tempfile
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from src.services.cache import FileCacheProvider
from src.services.gemini import GeminiClient
from src.core.interfaces import CacheProvider


@pytest.fixture  # type: ignore[untyped-decorator]
def temp_cache_dir() -> Generator[str, None, None]:
    """Create a temporary directory for cache testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_file_cache_provider_crud(temp_cache_dir: str) -> None:
    """Test Create, Read, Delete operations for FileCacheProvider."""
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "test_key"
    value = {"foo": "bar"}

    # Test Set
    provider.set(key, value)

    # Verify file exists - access private method for testing path logic
    # pylint: disable=protected-access
    cache_path = provider._get_cache_path(key)
    assert cache_path.exists()

    # Test Get
    retrieved = provider.get(key)
    assert retrieved == value

    # Test Delete
    provider.delete(key)
    assert not cache_path.exists()
    assert provider.get(key) is None


def test_file_cache_provider_miss(temp_cache_dir: str) -> None:
    """Test cache miss returns None."""
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    assert provider.get("non_existent") is None


def test_gemini_client_uses_cache() -> None:
    """Test that GeminiClient uses the injected cache provider."""
    # Setup Mock Cache
    mock_cache = Mock(spec=CacheProvider)
    mock_cache.get.return_value = None  # Start with cache miss

    # Setup Gemini Client with mock cache and mock API
    # We mock genai.Client to avoid actual API calls
    with patch("src.services.gemini.genai.Client") as mock_genai_cls:
        # Mock the client instance
        mock_client_instance = Mock()
        mock_genai_cls.return_value = mock_client_instance

        client = GeminiClient(api_key="fake_key", cache_provider=mock_cache)

        # Mock the API response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "title": "Test Idea",
            "description": "Test Desc",
            "slug": "test",
            "tech_stack": [],
            "features": []
        })
        mock_client_instance.models.generate_content.return_value = mock_response

        # 1. Test Cache Miss -> API Call -> Set Cache
        client.generate_idea()

        mock_cache.get.assert_called_once()
        assert mock_client_instance.models.generate_content.called
        mock_cache.set.assert_called_once()

        # 2. Test Cache Hit -> No API Call
        mock_cache.reset_mock()
        mock_client_instance.models.generate_content.reset_mock()
        mock_cache.set.reset_mock()

        # Simulate cache hit
        cached_value = {
            "title": "Cached Idea",
            "description": "Cached Desc",
            "slug": "cached",
            "tech_stack": [],
            "features": []
        }
        mock_cache.get.return_value = cached_value

        result = client.generate_idea()

        mock_cache.get.assert_called_once()
        assert not mock_client_instance.models.generate_content.called
        assert result == cached_value
