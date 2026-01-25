import pytest
from unittest.mock import MagicMock, patch
import json
from src.services.gemini import GeminiClient, GenerationError
from src.core.models import IdeaResponse, ProjectScaffold

@pytest.fixture
def mock_genai_client():
    with patch('src.services.gemini.genai.Client') as MockClient:
        yield MockClient

def test_generate_idea_success(mock_genai_client):
    # Setup
    client_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    expected_data = {
        "title": "Test App",
        "description": "A test app",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }
    mock_response.text = json.dumps(expected_data)
    client_instance.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="test_key")
    result = client.generate_idea(category="web_app")

    assert result == expected_data
    client_instance.models.generate_content.assert_called_once()

def test_generate_idea_invalid_json(mock_genai_client):
    # Setup
    client_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    client_instance.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="test_key")

    with pytest.raises(GenerationError) as excinfo:
        client.generate_idea()

    assert "Failed to parse Gemini response" in str(excinfo.value)

def test_extract_idea_from_text_success(mock_genai_client):
    # Setup
    client_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    expected_data = {
        "title": "Extracted App",
        "description": "An extracted app",
        "slug": "extracted-app",
        "tech_stack": ["python"],
        "features": ["feature1"]
    }
    mock_response.text = json.dumps(expected_data)
    client_instance.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="test_key")
    result = client.extract_idea_from_text("some text")

    assert result == expected_data

def test_generate_project_scaffold_success(mock_genai_client):
    # Setup
    client_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    expected_data = {
        "files": [],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    mock_response.text = json.dumps(expected_data)
    client_instance.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="test_key")
    idea_data = {
        "title": "Test App",
        "description": "Desc",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }
    result = client.generate_project_scaffold(idea_data)

    assert result == expected_data

def test_generate_project_scaffold_retry(mock_genai_client):
    # Setup
    client_instance = mock_genai_client.return_value

    # First call raises Exception
    # Second call returns success
    mock_response_success = MagicMock()
    expected_data = {
        "files": [],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    mock_response_success.text = json.dumps(expected_data)

    client_instance.models.generate_content.side_effect = [
        Exception("API Error"),
        mock_response_success
    ]

    client = GeminiClient(api_key="test_key")
    idea_data = {
        "title": "Test App",
        "description": "Desc",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }
    result = client.generate_project_scaffold(idea_data)

    assert result == expected_data
    assert client_instance.models.generate_content.call_count == 2
