"""Tests for GeminiClient caching integration."""

import json
import os
import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.core.interfaces import CacheProvider


@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock


@pytest.fixture
def mock_cache_provider():
    return MagicMock(spec=CacheProvider)


def test_gemini_init_with_cache(mock_genai_client, mock_cache_provider):
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        client = GeminiClient(cache_provider=mock_cache_provider)
        assert client.cache_provider == mock_cache_provider


def test_generate_content_uses_cache(mock_genai_client, mock_cache_provider):
    """Test that _generate_content returns cached value on hit."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        client = GeminiClient(cache_provider=mock_cache_provider)

        # Setup cache hit
        cached_response = {"title": "Cached Idea", "description": "Cached"}
        mock_cache_provider.get.return_value = cached_response

        # Call generate_idea (which calls _generate_content)
        result = client.generate_idea()

        # Verify result is from cache
        assert result == cached_response

        # Verify API was NOT called
        mock_genai_client.return_value.models.generate_content.assert_not_called()

        # Verify set was NOT called
        mock_cache_provider.set.assert_not_called()


def test_generate_content_cache_miss_and_set(mock_genai_client, mock_cache_provider):
    """Test that _generate_content calls API on cache miss and sets cache."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        client = GeminiClient(cache_provider=mock_cache_provider)

        # Setup cache miss
        mock_cache_provider.get.return_value = None

        # Setup API response
        api_response = {"title": "API Idea", "description": "Fresh"}
        mock_response = MagicMock()
        mock_response.text = json.dumps(api_response)
        client.client.models.generate_content.return_value = mock_response

        # Call generate_idea
        result = client.generate_idea()

        # Verify result is from API
        assert result == api_response

        # Verify API WAS called
        client.client.models.generate_content.assert_called_once()

        # Verify cache was updated
        mock_cache_provider.set.assert_called_once()
        args, _ = mock_cache_provider.set.call_args
        assert args[1] == api_response
