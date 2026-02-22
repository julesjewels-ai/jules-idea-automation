"""Integration tests for Gemini Caching."""

import pytest
import hashlib
import json
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from pathlib import Path
from typing import Generator
from src.services.cache import FileCacheProvider
from src.core.models import IdeaResponse

@pytest.fixture  # type: ignore
def mock_genai_client() -> Generator[MagicMock, None, None]:
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture  # type: ignore
def cache_dir(tmp_path: Path) -> Path:
    return tmp_path / "cache"

@pytest.fixture  # type: ignore
def provider(cache_dir: Path) -> FileCacheProvider:
    return FileCacheProvider(cache_dir=str(cache_dir))

def test_gemini_uses_cache(mock_genai_client: MagicMock, provider: FileCacheProvider) -> None:
    """Test that GeminiClient uses the cache."""
    client = GeminiClient(api_key="test", cache=provider)

    # Mock API response
    mock_response = MagicMock()
    expected_data = {
        "title": "Cached Idea",
        "description": "Desc",
        "slug": "cached-idea",
        "tech_stack": [],
        "features": []
    }
    mock_response.text = json.dumps(expected_data)
    client.client.models.generate_content.return_value = mock_response

    # First call: Should hit API and cache result
    result1 = client.generate_idea()
    assert result1["title"] == "Cached Idea"
    client.client.models.generate_content.assert_called_once()

    # Second call: Should hit cache
    result2 = client.generate_idea()
    assert result2["title"] == "Cached Idea"

    # API should strictly be called once
    assert client.client.models.generate_content.call_count == 1

def test_gemini_cache_miss(mock_genai_client: MagicMock, provider: FileCacheProvider) -> None:
    """Test that GeminiClient handles cache miss."""
    client = GeminiClient(api_key="test", cache=provider)

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "New Idea",
        "description": "Desc",
        "slug": "new-idea",
        "tech_stack": [],
        "features": []
    })
    client.client.models.generate_content.return_value = mock_response

    # Cache miss
    result = client.generate_idea()
    assert result["title"] == "New Idea"
    client.client.models.generate_content.assert_called_once()
