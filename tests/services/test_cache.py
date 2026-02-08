"""Tests for Cache Service and Integration."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.cache import FileCacheProvider, InMemoryCacheProvider
from src.services.gemini import GeminiClient


def test_in_memory_cache() -> None:
    """Test InMemoryCacheProvider basic operations."""
    cache = InMemoryCacheProvider()
    cache.set("key", "value")
    assert cache.get("key") == "value"
    cache.delete("key")
    assert cache.get("key") is None


def test_file_cache_crud(tmp_path: Path) -> None:
    """Test FileCacheProvider CRUD operations."""
    cache_dir = tmp_path / "cache"
    cache = FileCacheProvider(cache_dir=str(cache_dir))

    # Test Set/Get
    cache.set("key1", {"foo": "bar"})
    result = cache.get("key1")
    assert result == {"foo": "bar"}

    # Test persistence (new instance pointing to same dir)
    cache2 = FileCacheProvider(cache_dir=str(cache_dir))
    assert cache2.get("key1") == {"foo": "bar"}

    # Test Delete
    cache.delete("key1")
    assert cache.get("key1") is None
    assert cache2.get("key1") is None


def test_file_cache_expiry(tmp_path: Path) -> None:
    """Test FileCacheProvider TTL logic."""
    cache_dir = tmp_path / "cache"
    cache = FileCacheProvider(cache_dir=str(cache_dir))

    cache.set("expired", "value", ttl=-1)  # Already expired
    assert cache.get("expired") is None

    cache.set("valid", "value", ttl=3600)
    assert cache.get("valid") == "value"


def test_gemini_client_uses_cache() -> None:
    """Test that GeminiClient retrieves data from cache and skips API call."""
    cache = InMemoryCacheProvider()
    # Pre-populate cache with exact prompt expected from generate_idea
    base_prompt = (
        "Generate a creative web application idea. "
        "Focus on modern frontend frameworks and responsive design."
    )
    prompt = (
        f"{base_prompt} Include recommended tech stack and key MVP features."
    )

    cached_response = {
        "title": "Cached Idea",
        "description": "This is cached",
        "slug": "cached-idea",
        "tech_stack": [],
        "features": []
    }
    cache.set(prompt, cached_response)

    # Mock API Key to avoid config error
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
        client = GeminiClient(cache=cache)
        # Mock internal client to ensure it's NOT called
        client.client = MagicMock()

        result = client.generate_idea(category="web_app")

        assert result == cached_response
        # Verify API was NOT called
        client.client.models.generate_content.assert_not_called()


def test_gemini_client_populates_cache() -> None:
    """Test that GeminiClient stores successful API responses in cache."""
    cache = InMemoryCacheProvider()

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
        client = GeminiClient(cache=cache)

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "title": "New Idea",
            "description": "Generated from API",
            "slug": "new-idea",
            "tech_stack": [],
            "features": []
        })
        client.client.models.generate_content = (
            MagicMock(return_value=mock_response)
        )

        result = client.generate_idea(category="web_app")

        assert result["title"] == "New Idea"

        # Verify it's now in cache
        assert len(cache._cache) == 1
        cached_val = list(cache._cache.values())[0]["value"]
        assert cached_val["title"] == "New Idea"
