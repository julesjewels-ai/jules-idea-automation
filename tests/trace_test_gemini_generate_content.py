import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from typing import Any, Optional, Union, Type
import json
from google.genai import errors
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError
from src.core.interfaces import CacheProvider

@pytest.fixture
def mock_cache_provider(mocker: MockerFixture) -> MagicMock:
    return mocker.MagicMock(spec=CacheProvider)

@pytest.fixture
def client(mocker: MockerFixture, mock_cache_provider: MagicMock) -> GeminiClient:
    # Patch the genai module in the target file to prevent real API calls
    mocker.patch("src.services.gemini.genai")
    # Initialize client with the mock cache provider
    # We pass api_key to avoid env var check failure
    return GeminiClient(api_key="test_key", cache_provider=mock_cache_provider)

# Helper to create an APIError with the required structure
def create_api_error(code: int, message: str) -> errors.APIError:
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": {"message": message}}
    mock_response.status_code = code
    return errors.APIError(code=code, response=mock_response)

# Simple class to use as schema that avoids MagicMock recursion/type issues
class SimpleSchema:
    pass

@pytest.mark.parametrize("scenario, cache_data, api_response_text, api_error, expected_result", [
    (
        "cache_hit",
        {"data": "cached_value"},
        None,
        None,
        {"data": "cached_value"}
    ),
    (
        "cache_miss_success",
        None,
        json.dumps({"data": "new_value"}),
        None,
        {"data": "new_value"}
    ),
    (
        "json_decode_error",
        None,
        "invalid_json_response",
        None,
        GenerationError
    ),
    (
        "api_error_400",
        None,
        None,
        create_api_error(400, "API key not valid"),
        GenerationError
    ),
    (
        "generic_exception",
        None,
        None,
        Exception("Unexpected network failure"),
        GenerationError
    ),
])
def test_generate_content_behavior(
    mocker: MockerFixture,
    client: GeminiClient,
    mock_cache_provider: MagicMock,
    scenario: str,
    cache_data: Optional[dict[str, Any]],
    api_response_text: Optional[str],
    api_error: Optional[Exception],
    expected_result: Union[dict[str, Any], Type[Exception]]
) -> None:
    # Setup
    prompt = "trace_test_prompt"
    error_tip = "Test tip"

    # Use a real class instead of a Mock for schema to avoid serialization issues
    schema_mock = SimpleSchema

    # Configure Cache Behavior
    if scenario == "cache_hit":
        mock_cache_provider.get.return_value = cache_data
    else:
        mock_cache_provider.get.return_value = None

    # Configure API Behavior
    # client.client is the genai.Client instance
    # client.client.models is the service
    mock_models = client.client.models

    if api_error:
        mock_models.generate_content.side_effect = api_error
    else:
        mock_response = MagicMock()
        mock_response.text = api_response_text
        mock_models.generate_content.return_value = mock_response

    # Execution & Validation
    if isinstance(expected_result, type) and issubclass(expected_result, Exception):
        with pytest.raises(expected_result):
            client._generate_content(prompt, schema_mock, error_tip)
    else:
        result = client._generate_content(prompt, schema_mock, error_tip)
        assert result == expected_result

    # Side Effect Verification
    if scenario == "cache_hit":
        mock_cache_provider.get.assert_called_once()
        mock_models.generate_content.assert_not_called()
        mock_cache_provider.set.assert_not_called()

    elif scenario == "cache_miss_success":
        mock_cache_provider.get.assert_called_once()
        mock_models.generate_content.assert_called_once()
        mock_cache_provider.set.assert_called_once()

        # Verify call args for set to ensure it's caching what we expect
        args, _ = mock_cache_provider.set.call_args
        assert args[1] == expected_result
