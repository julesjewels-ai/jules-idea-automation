import pytest
from unittest.mock import Mock, patch
import json
import os
from google.genai import errors
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError, ConfigurationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture
def client(mock_genai_client):
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        return GeminiClient()

def test_generate_content_success(client):
    """Test happy path for _generate_content."""
    mock_response = Mock()
    expected_data = {"key": "value"}
    mock_response.text = json.dumps(expected_data)
    client.client.models.generate_content.return_value = mock_response

    result = client._generate_content("prompt", dict, "error tip")
    assert result == expected_data

@pytest.mark.parametrize("side_effect, expected_message_part, expected_tip_part", [
    (
        errors.APIError(code=400, response_json={"message": "API key not valid"}),
        "API key not valid",
        "Your GEMINI_API_KEY seems invalid"
    ),
    (
        errors.APIError(code=400, response_json={"message": "Bad Request"}),
        "400",
        "Your GEMINI_API_KEY seems invalid"
    ),
    (
        errors.APIError(code=429, response_json={"message": "Too Many Requests"}),
        "429",
        "You have exceeded your API quota"
    ),
    (
        errors.APIError(code=500, response_json={"message": "Quota exceeded"}),
        "Quota exceeded",
        "You have exceeded your API quota"
    ),
    (
        errors.APIError(code=403, response_json={"message": "Forbidden"}),
        "403",
        "You don't have permission"
    ),
    (
        errors.APIError(code=500, response_json={"message": "Server Error"}),
        "Server Error",
        "Check your internet connection"
    ),
    (
        json.JSONDecodeError("msg", "doc", 0),
        "Failed to parse Gemini response",
        "error tip"  # This is passed as argument
    ),
    (
        Exception("Something went wrong"),
        "Unexpected error",
        "Check your network connection"
    )
])
def test_generate_content_error_mapping(client, side_effect, expected_message_part, expected_tip_part):
    """Test error mapping logic in _generate_content."""
    client.client.models.generate_content.side_effect = side_effect

    with pytest.raises(GenerationError) as excinfo:
        client._generate_content("prompt", dict, "error tip")

    error = excinfo.value
    assert expected_message_part in str(error)
    assert expected_tip_part in error.tip
