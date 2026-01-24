import pytest
from unittest.mock import MagicMock, patch, ANY
import json
import os

from src.services.gemini import GeminiClient
from src.utils.errors import ConfigurationError, GenerationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture
def client(mock_genai_client):
    # Pass a dummy key to bypass env check
    return GeminiClient(api_key="test_key")

def test_init_no_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError):
            GeminiClient()

def test_generate_idea_success(client, mock_genai_client):
    # Setup mock response
    mock_response = MagicMock()
    expected_data = {"title": "Test App", "description": "A test app", "slug": "test-app", "tech_stack": [], "features": []}
    mock_response.text = json.dumps(expected_data)

    # Configure the mock client instance returned by the class constructor mock
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    result = client.generate_idea("web_app")

    assert result == expected_data
    mock_instance.models.generate_content.assert_called_once()

def test_generate_idea_json_error(client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = "Invalid JSON"

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as exc:
        client.generate_idea()

    assert "invalid JSON" in str(exc.value.tip)

def test_extract_idea_from_text_success(client, mock_genai_client):
    mock_response = MagicMock()
    expected_data = {"title": "Extracted", "description": "Desc", "slug": "extracted", "tech_stack": [], "features": []}
    mock_response.text = json.dumps(expected_data)

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    result = client.extract_idea_from_text("some text content")

    assert result == expected_data

def test_generate_project_scaffold_success(client, mock_genai_client):
    mock_response = MagicMock()
    expected_data = {"files": [], "requirements": [], "run_command": "cmd"}
    mock_response.text = json.dumps(expected_data)

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    idea_data = {"title": "T", "description": "D", "slug": "s", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data)

    assert result == expected_data

def test_generate_project_scaffold_retry_success(client, mock_genai_client):
    # First attempt fails, second succeeds
    mock_response = MagicMock()
    mock_response.text = json.dumps({"files": []})

    mock_instance = mock_genai_client.return_value
    # Side effect: first raise Exception, then return success
    mock_instance.models.generate_content.side_effect = [Exception("API Error"), mock_response]

    idea_data = {"title": "T", "description": "D", "slug": "s", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data)

    assert result == {"files": []}
    assert mock_instance.models.generate_content.call_count == 2

def test_generate_project_scaffold_failure_fallback(client, mock_genai_client):
    # All attempts fail
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.side_effect = Exception("API Error")

    idea_data = {"title": "Fallback", "description": "Desc", "slug": "f", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data, max_retries=1)

    # Should return fallback scaffold
    assert result["run_command"] == "python main.py"
    assert any(f["path"] == "main.py" for f in result["files"])
    # 1 initial + 1 retry = 2 calls
    assert mock_instance.models.generate_content.call_count == 2
