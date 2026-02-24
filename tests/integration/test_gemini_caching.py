import pytest
import json
from unittest.mock import Mock
from typing import Any
from src.services.gemini import GeminiClient
from src.services.cache import FileCacheProvider

class MockResponse:
    def __init__(self, text: str) -> None:
        self.text = text

def test_gemini_client_caching_hit(mocker: Any, tmp_path: Any) -> None:
    """Test that a second call with the same parameters hits the cache."""
    # Mock genai.Client
    mock_genai = mocker.patch("src.services.gemini.genai")
    mock_client_instance = mock_genai.Client.return_value
    mock_generate = mock_client_instance.models.generate_content

    # Prepare mock response
    idea_data = {
        "title": "Test Idea",
        "description": "Desc",
        "slug": "slug",
        "tech_stack": [],
        "features": []
    }
    mock_response_json = json.dumps(idea_data)
    mock_generate.return_value = MockResponse(mock_response_json)

    # Setup
    cache_dir = str(tmp_path / "cache")
    cache_provider = FileCacheProvider(cache_dir=cache_dir)
    client = GeminiClient(api_key="fake_key", cache_provider=cache_provider)

    # First call - should hit API
    result1 = client.generate_idea(category="test")
    assert result1["title"] == "Test Idea"
    assert mock_generate.call_count == 1

    # Second call - should hit cache
    result2 = client.generate_idea(category="test")
    assert result2["title"] == "Test Idea"
    assert mock_generate.call_count == 1  # Still 1

def test_gemini_client_caching_miss(mocker: Any, tmp_path: Any) -> None:
    """Test that different parameters cause a cache miss."""
    # Mock genai.Client
    mock_genai = mocker.patch("src.services.gemini.genai")
    mock_client_instance = mock_genai.Client.return_value
    mock_generate = mock_client_instance.models.generate_content

    idea_data = {
        "title": "Idea",
        "description": "D",
        "slug": "s",
        "tech_stack": [],
        "features": []
    }
    mock_response_json = json.dumps(idea_data)
    mock_generate.return_value = MockResponse(mock_response_json)

    cache_dir = str(tmp_path / "cache")
    cache_provider = FileCacheProvider(cache_dir=cache_dir)
    client = GeminiClient(api_key="fake_key", cache_provider=cache_provider)

    client.generate_idea(category="web_app")
    client.generate_idea(category="cli_tool")

    # Should be 2 calls because prompts differ
    assert mock_generate.call_count == 2
