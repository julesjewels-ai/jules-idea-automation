"""Integration tests for caching service."""

import json
import os
import shutil
import pytest
from unittest.mock import MagicMock

from src.services.cache import FileCacheProvider
from src.services.gemini import GeminiClient


@pytest.fixture
def test_cache_dir():
    """Fixture to provide a temporary cache directory."""
    path = ".jules/test_cache"
    if os.path.exists(path):
        shutil.rmtree(path)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


def test_gemini_caching(test_cache_dir):
    """Test that GeminiClient uses the cache."""
    cache = FileCacheProvider(cache_dir=test_cache_dir)
    # Pass a fake key so it doesn't try to look up env var or fail validation
    client = GeminiClient(api_key="fake_key", cache=cache)

    # Mock the internal client.models.generate_content
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Cached Idea",
        "description": "This is a cached idea.",
        "slug": "cached-idea",
        "tech_stack": ["python"],
        "features": ["caching"]
    })

    # We need to mock the genai.Client inside GeminiClient
    client.client = MagicMock()
    client.client.models.generate_content.return_value = mock_response

    # First call - should hit the API (mock)
    result1 = client.generate_idea()

    assert result1["title"] == "Cached Idea"
    client.client.models.generate_content.assert_called_once()

    # Verify cache file exists
    assert os.path.exists(test_cache_dir)
    assert len(os.listdir(test_cache_dir)) == 1

    # Second call - should hit the cache
    result2 = client.generate_idea()

    assert result2["title"] == "Cached Idea"
    # Call count should still be 1
    client.client.models.generate_content.assert_called_once()

    # Modify cache file manually to prove it's reading from file
    cache_file = os.path.join(test_cache_dir, os.listdir(test_cache_dir)[0])
    with open(cache_file, "w") as f:
        json.dump({
            "title": "Modified Cached Idea",
            "description": "Modified",
            "slug": "modified",
            "tech_stack": [],
            "features": []
        }, f)

    # Third call - should return modified data
    result3 = client.generate_idea()
    assert result3["title"] == "Modified Cached Idea"
    client.client.models.generate_content.assert_called_once()
