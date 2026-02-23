"""Integration tests for Gemini client caching."""
import pytest
from unittest.mock import MagicMock
from src.services.gemini import GeminiClient
from src.services.cache import FileCacheProvider
from src.core.models import IdeaResponse


from pathlib import Path
from pytest_mock import MockerFixture

def test_gemini_caching(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test that GeminiClient uses the cache."""
    cache = FileCacheProvider(cache_dir=str(tmp_path))

    # Mock the API client
    mock_genai_client = mocker.patch("src.services.gemini.genai.Client")
    mock_model = MagicMock()
    mock_genai_client.return_value.models = mock_model

    # Setup expected response
    expected_data = {
        "title": "Test Idea",
        "description": "A test idea",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }

    mock_response = MagicMock()
    mock_response.text = '{"title": "Test Idea", "description": "A test idea", "slug": "test-idea", "tech_stack": ["python"], "features": ["feature1"]}'
    mock_model.generate_content.return_value = mock_response

    # Initialize GeminiClient with cache
    client = GeminiClient(api_key="fake_key", cache_provider=cache)

    # First call: Should hit the API
    result1 = client.generate_idea(category="test")
    assert result1 == expected_data
    assert mock_model.generate_content.call_count == 1

    # Second call: Should hit the cache
    result2 = client.generate_idea(category="test")
    assert result2 == expected_data
    assert mock_model.generate_content.call_count == 1  # Call count should not increase

    # Verify cache content
    # We need to construct the key to verify
    # But since we use internal method _get_cache_key, we can just check if file exists in tmp_path
    assert len(list(tmp_path.glob("*.json"))) == 1
