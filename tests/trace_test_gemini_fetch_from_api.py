import pytest
from pytest_mock import MockerFixture
import json
from unittest.mock import MagicMock
from typing import Any

from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError
from google.genai.errors import APIError
from pydantic import BaseModel

class DummySchema(BaseModel):
    key: str

@pytest.fixture
def mock_context(mocker: MockerFixture) -> dict[str, Any]:
    mock_cache = mocker.MagicMock()
    mock_cache.set = mocker.MagicMock()

    mock_client = mocker.MagicMock()
    mock_client.models.generate_content = mocker.MagicMock()

    # Pass api_key to avoid ConfigurationError
    gemini_client = GeminiClient(api_key="test_key", cache_provider=mock_cache)
    gemini_client.client = mock_client

    return {
        "client": gemini_client,
        "mock_cache": mock_cache,
        "mock_genai_client": mock_client
    }

def create_api_error(message: str) -> APIError:
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": {"message": message}}
    return APIError(code=500, response=mock_response)

@pytest.mark.parametrize("prompt, schema, error_tip, cache_key, mock_response_text, side_effect, expected", [
    (
        "valid_prompt",
        DummySchema,
        "tip",
        "cache_key_1",
        '{"key": "value"}',
        None,
        {"key": "value"}
    ),  # Happy Path (Schema Validated)
    (
        "valid_prompt",
        None,
        "tip",
        "cache_key_2",
        '{"raw": "dict"}',
        None,
        {"raw": "dict"}
    ),  # Happy Path (Raw Return)
    (
        "bad_json_prompt",
        DummySchema,
        "json error tip",
        "cache_key_3",
        '{bad_json',
        None,
        GenerationError  # Edge Case (JSONDecodeError)
    ),
    (
        "api_error_prompt",
        DummySchema,
        "api error tip",
        "cache_key_4",
        None,
        create_api_error("API Error"),
        GenerationError  # Error State (APIError)
    ),
    (
        "generic_error_prompt",
        DummySchema,
        "generic tip",
        "cache_key_5",
        None,
        ValueError("Something went wrong"),
        GenerationError  # Error State (Generic Exception)
    ),
])
def test_fetch_from_api_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    prompt: str,
    schema: Any,
    error_tip: str,
    cache_key: str,
    mock_response_text: str | None,
    side_effect: Exception | None,
    expected: Any
) -> None:
    gemini_client: GeminiClient = mock_context["client"]
    mock_cache = mock_context["mock_cache"]
    mock_genai_client = mock_context["mock_genai_client"]

    if side_effect:
        mock_genai_client.models.generate_content.side_effect = side_effect
    else:
        mock_response = mocker.MagicMock()
        mock_response.text = mock_response_text
        mock_genai_client.models.generate_content.return_value = mock_response

    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            gemini_client._fetch_from_api(prompt, schema, error_tip, cache_key)
    else:
        result = gemini_client._fetch_from_api(prompt, schema, error_tip, cache_key)
        assert result == expected

        # Verify side effect: CacheProvider.set is called
        if cache_key and mock_response_text:
            mock_cache.set.assert_called_once_with(cache_key, json.loads(mock_response_text))
