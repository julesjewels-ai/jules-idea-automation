import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient, GenerationError
from src.core.models import IdeaResponse, ProjectScaffold
import json
from google.genai import types

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture
def client(mock_genai_client):
    # Set API key to avoid ConfigurationError
    return GeminiClient(api_key="fake-key")

def test_generate_idea_success(client, mock_genai_client):
    # Setup mock response
    mock_response = MagicMock()
    expected_data = {
        "title": "Test App",
        "description": "A test app",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }
    mock_response.text = json.dumps(expected_data)

    # Configure the mock client instance
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    # Call the method
    result = client.generate_idea(category="web_app")

    # Verify
    assert result == expected_data
    mock_instance.models.generate_content.assert_called_once()
    args, kwargs = mock_instance.models.generate_content.call_args
    assert kwargs["config"].response_schema == IdeaResponse

def test_generate_idea_json_error(client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = "invalid json"

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as exc:
        client.generate_idea()

    assert "Failed to parse Gemini response" in str(exc.value)

def test_extract_idea_from_text_success(client, mock_genai_client):
    mock_response = MagicMock()
    expected_data = {
        "title": "Extracted App",
        "description": "An extracted app",
        "slug": "extracted-app",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }
    mock_response.text = json.dumps(expected_data)

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    result = client.extract_idea_from_text("some text content")

    assert result == expected_data
    mock_instance.models.generate_content.assert_called_once()

def test_generate_project_scaffold_success(client, mock_genai_client):
    mock_response = MagicMock()
    expected_data = {
        "files": [],
        "requirements": [],
        "run_command": "echo hello"
    }
    mock_response.text = json.dumps(expected_data)

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    idea_data = {
        "title": "Test App",
        "description": "A test app",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }

    result = client.generate_project_scaffold(idea_data)

    assert result == expected_data
    mock_instance.models.generate_content.assert_called_once()
    args, kwargs = mock_instance.models.generate_content.call_args
    assert kwargs["config"].response_schema == ProjectScaffold

def test_generate_project_scaffold_retry_success(client, mock_genai_client):
    # Fail first, succeed second
    mock_response_fail = MagicMock()
    mock_response_fail.text = "invalid json"

    mock_response_success = MagicMock()
    mock_response_success.text = json.dumps({
        "files": [], "requirements": [], "run_command": "echo hello"
    })

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.side_effect = [
        mock_response_fail,
        mock_response_success
    ]

    idea_data = {"title": "T", "description": "D", "slug": "s", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "echo hello"
    assert mock_instance.models.generate_content.call_count == 2

def test_generate_project_scaffold_fallback(client, mock_genai_client):
    # Always fail
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.side_effect = Exception("API Error")

    idea_data = {"title": "T", "description": "D", "slug": "s", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data, max_retries=1)

    # Should return fallback
    assert result["run_command"] == "python main.py"
    # Check that we got fallback content (e.g. main.py)
    files = {f["path"]: f["content"] for f in result["files"]}
    assert "main.py" in files
    assert mock_instance.models.generate_content.call_count == 2 # 0 + 1 retry
