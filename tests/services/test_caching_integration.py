"""Integration tests for GeminiClient caching."""

import json
import hashlib
from typing import Any, Optional, cast, Generator
from unittest.mock import MagicMock, patch

import pytest
from src.services.gemini import GeminiClient
# CacheProvider is a Protocol, so we don't strictly need to inherit for runtime,
# but it helps structure.


class MockCacheProvider:
    """Mock cache provider for testing."""

    def __init__(self) -> None:
        self.store: dict[str, Any] = {}
        self.get_called_with: Optional[str] = None
        self.set_called_with: Optional[tuple[str, Any]] = None

    def get(self, key: str) -> Optional[Any]:
        self.get_called_with = key
        return self.store.get(key)

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        self.set_called_with = (key, value)
        self.store[key] = value

    def delete(self, key: str) -> None:
        if key in self.store:
            del self.store[key]


@pytest.fixture
def mock_genai_client() -> Generator[MagicMock, None, None]:
    """Mock the Google GenAI client."""
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock


def test_gemini_client_uses_cache(mock_genai_client: MagicMock) -> None:
    """Test that GeminiClient uses the cache."""
    cache = MockCacheProvider()

    # Instantiate client with cache
    # MockCacheProvider satisfies the Protocol via duck typing
    client = GeminiClient(api_key="fake_key", cache_provider=cache)

    # Mock the API response
    mock_response = MagicMock()
    mock_response.text = json.dumps({"title": "New Idea"})

    # Helper to satisfy mypy for mocked attributes
    mock_models = cast(MagicMock, client.client.models)
    mock_models.generate_content.return_value = mock_response

    # 1. First call - should be a cache miss
    prompt = "Test Prompt"
    expected_hash = hashlib.sha256(prompt.encode()).hexdigest()
    expected_key = f"gemini:{client.model_name}:{expected_hash}"

    result = client._generate_content(prompt, None, "error")

    assert result == {"title": "New Idea"}
    assert cache.get_called_with == expected_key
    assert cache.set_called_with is not None
    assert cache.set_called_with[0] == expected_key
    assert cache.set_called_with[1] == {"title": "New Idea"}

    # Verify API was called
    mock_models.generate_content.assert_called_once()

    # 2. Second call - should be a cache hit
    # Reset API mock to verify it's NOT called
    mock_models.generate_content.reset_mock()

    result2 = client._generate_content(prompt, None, "error")

    assert result2 == {"title": "New Idea"}
    assert cache.get_called_with == expected_key

    # Verify API was NOT called
    mock_models.generate_content.assert_not_called()
