"""Integration tests for caching in GeminiClient."""

from unittest.mock import MagicMock

from src.services.gemini import GeminiClient


class MockCache:
    """Mock cache provider."""

    def __init__(self):
        self.store = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value, ttl=None):
        self.store[key] = value


def test_gemini_uses_cache(monkeypatch):
    """Test that GeminiClient checks cache before API call."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

    cache = MockCache()
    client = GeminiClient(api_key="fake_key", cache_provider=cache)

    # Mock the internal client
    client.client = MagicMock()

    # Pre-populate cache
    prompt = "Test Prompt"
    cache_key = f"gemini:{client.model_name}:{prompt}"
    expected_response = {"result": "cached"}
    cache.set(cache_key, expected_response)

    # Call _generate_content
    result = client._generate_content(prompt, None, "error")

    assert result == expected_response
    # Ensure API was NOT called
    client.client.models.generate_content.assert_not_called()


def test_gemini_populates_cache(monkeypatch):
    """Test that GeminiClient populates cache after API call."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

    cache = MockCache()
    client = GeminiClient(api_key="fake_key", cache_provider=cache)

    # Mock the internal client response
    client.client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"result": "generated"}'
    client.client.models.generate_content.return_value = mock_response

    prompt = "New Prompt"
    cache_key = f"gemini:{client.model_name}:{prompt}"

    # Cache should be empty initially
    assert cache.get(cache_key) is None

    result = client._generate_content(prompt, None, "error")

    assert result == {"result": "generated"}
    # Ensure API WAS called
    client.client.models.generate_content.assert_called_once()
    # Ensure cache was populated
    assert cache.get(cache_key) == {"result": "generated"}
