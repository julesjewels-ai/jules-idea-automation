"""Integration tests for Gemini client caching."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.services.cache import FileCacheProvider
from src.services.gemini import GeminiClient


@pytest.fixture
def mock_gemini_response(mocker: Any) -> MagicMock:
    """Mock the Google GenAI response."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "title": "Test App",
            "description": "A test application",
            "slug": "test-app",
            "tech_stack": ["Python"],
            "features": ["Feature 1"],
        }
    )
    return mock_response


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for the cache."""
    return tmp_path / ".cache" / "gemini"


def test_gemini_caching(mocker: Any, mock_gemini_response: MagicMock, temp_cache_dir: Path) -> None:
    """Test that GeminiClient caches responses correctly."""

    # Mock the genai.Client
    mock_client_cls = mocker.patch("src.services.gemini.genai.Client")
    mock_client_instance = mock_client_cls.return_value
    mock_client_instance.models.generate_content.return_value = mock_gemini_response

    # Initialize cache provider with temp dir
    cache_provider = FileCacheProvider(cache_dir=str(temp_cache_dir))

    # Initialize GeminiClient with cache
    client = GeminiClient(api_key="fake-key", cache_provider=cache_provider)

    # First call - should hit the API (mock)
    result1 = client.generate_idea()

    assert result1["title"] == "Test App"
    assert mock_client_instance.models.generate_content.call_count == 1

    # Verify cache file created
    # We need to reconstruct the key to find the file
    # The prompt is constructed inside generate_idea, so we need to know what it is or check any file in dir
    files = list(temp_cache_dir.glob("*.json"))
    assert len(files) == 1

    # Verify cache content
    cached_content = json.loads(files[0].read_text())
    assert cached_content["title"] == "Test App"

    # Second call - should hit the cache (no API call)
    result2 = client.generate_idea()

    assert result2["title"] == "Test App"
    assert mock_client_instance.models.generate_content.call_count == 1  # Count should not increase


def test_gemini_caching_different_prompts(mocker: Any, mock_gemini_response: MagicMock, temp_cache_dir: Path) -> None:
    """Test that different prompts generate different cache entries."""

    mock_client_cls = mocker.patch("src.services.gemini.genai.Client")
    mock_client_instance = mock_client_cls.return_value
    mock_client_instance.models.generate_content.return_value = mock_gemini_response

    cache_provider = FileCacheProvider(cache_dir=str(temp_cache_dir))
    client = GeminiClient(api_key="fake-key", cache_provider=cache_provider)

    # Call with category 'web_app'
    client.generate_idea(category="web_app")

    # Call with category 'cli_tool'
    client.generate_idea(category="cli_tool")

    assert mock_client_instance.models.generate_content.call_count == 2

    files = list(temp_cache_dir.glob("*.json"))
    assert len(files) == 2
