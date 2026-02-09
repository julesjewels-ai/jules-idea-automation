"""Tests for caching service."""

import json
import os
import shutil
import tempfile
from typing import Generator, Any, Optional
from unittest.mock import Mock, patch

import pytest
from src.services.cache import FileCacheProvider
from src.services.gemini import GeminiClient, CATEGORY_PROMPTS
from src.core.interfaces import CacheProvider
from src.utils.errors import CacheError


@pytest.fixture
def temp_cache_dir() -> Generator[str, None, None]:
    """Provide a temporary directory for cache testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_file_cache_provider_lifecycle(temp_cache_dir: str) -> None:
    """Test that FileCacheProvider correctly sets and gets values."""
    provider = FileCacheProvider(cache_dir=temp_cache_dir)
    key = "test_key"
    value = {"data": "test_value", "number": 42}

    # Should be None initially
    assert provider.get(key) is None

    # Set value
    provider.set(key, value)

    # Get value
    retrieved = provider.get(key)
    assert retrieved == value

    # Verify file existence
    files = os.listdir(temp_cache_dir)
    assert len(files) == 1


def test_file_cache_persistence(temp_cache_dir: str) -> None:
    """Test that cache persists across instances."""
    provider1 = FileCacheProvider(cache_dir=temp_cache_dir)
    provider1.set("persist_key", "persist_value")

    provider2 = FileCacheProvider(cache_dir=temp_cache_dir)
    assert provider2.get("persist_key") == "persist_value"


def test_cache_initialization_error() -> None:
    """Test that FileCacheProvider raises CacheError on init failure."""
    with patch("os.makedirs", side_effect=OSError("Permission denied")):
        with pytest.raises(CacheError) as excinfo:
            FileCacheProvider(cache_dir="/root/forbidden")
        assert "Failed to create cache directory" in str(excinfo.value)


class MockCache(CacheProvider):
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        return self.store.get(key)

    def set(self, key: str, value: Any) -> None:
        self.store[key] = value


def test_gemini_client_uses_cache() -> None:
    """Test that GeminiClient checks cache before API call."""
    mock_cache = MockCache()

    # Pre-populate cache
    base_prompt = CATEGORY_PROMPTS["web_app"]
    prompt = f"{base_prompt} Include recommended tech stack and key MVP features."
    model_name = "gemini-3-pro-preview"
    expected_key = f"{model_name}:{prompt}"

    cached_response = {
        "title": "Cached Idea",
        "description": "This is from cache",
        "slug": "cached-idea",
        "tech_stack": [],
        "features": []
    }
    mock_cache.set(expected_key, cached_response)

    # Initialize client with mock cache and mock API key
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        client = GeminiClient(cache_provider=mock_cache)

        # Mock the API client to ensure it's NOT called
        client.client = Mock()
        client.client.models.generate_content.side_effect = Exception("API should not be called")

        # Call generate_idea
        result = client.generate_idea(category="web_app")

        assert result == cached_response


def test_gemini_client_populates_cache() -> None:
    """Test that GeminiClient saves to cache after API call."""
    mock_cache = MockCache()

    # Initialize client with mock cache
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        client = GeminiClient(cache_provider=mock_cache)

        # Mock API response
        mock_response = Mock()
        expected_data = {
            "title": "New Idea",
            "description": "Generated from API",
            "slug": "new-idea",
            "tech_stack": [],
            "features": []
        }
        mock_response.text = json.dumps(expected_data)
        client.client.models.generate_content = Mock(return_value=mock_response)

        # Call generate_idea
        client.generate_idea(category="web_app")

        # Verify cache was populated
        base_prompt = CATEGORY_PROMPTS["web_app"]
        prompt = f"{base_prompt} Include recommended tech stack and key MVP features."
        key = f"{client.model_name}:{prompt}"

        assert mock_cache.get(key) == expected_data
