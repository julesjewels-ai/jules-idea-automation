import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError, ConfigurationError
import json

@pytest.fixture
def mock_genai_client():
    with patch('src.services.gemini.genai.Client') as mock_client:
        yield mock_client

@pytest.fixture
def gemini_client(mock_genai_client):
    with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
        return GeminiClient()

def test_init_no_api_key():
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ConfigurationError):
            GeminiClient(api_key=None)

def test_generate_idea_success(gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Test Idea",
        "description": "A test description",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    })
    gemini_client.client.models.generate_content.return_value = mock_response

    result = gemini_client.generate_idea()

    assert result["title"] == "Test Idea"
    gemini_client.client.models.generate_content.assert_called_once()

def test_generate_idea_json_error(gemini_client):
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    gemini_client.client.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as exc:
        gemini_client.generate_idea()

    assert "Failed to parse Gemini response" in str(exc.value)

def test_extract_idea_from_text_success(gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Extracted Idea",
        "description": "Extracted description",
        "slug": "extracted-idea",
        "tech_stack": ["node"],
        "features": ["feature2"]
    })
    gemini_client.client.models.generate_content.return_value = mock_response

    result = gemini_client.extract_idea_from_text("some text content")

    assert result["title"] == "Extracted Idea"
    gemini_client.client.models.generate_content.assert_called_once()

def test_generate_project_scaffold_success(gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "echo hello"
    })
    gemini_client.client.models.generate_content.return_value = mock_response

    idea_data = {
        "title": "My App",
        "description": "App desc",
        "slug": "my-app",
        "tech_stack": [],
        "features": []
    }
    result = gemini_client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "echo hello"
    gemini_client.client.models.generate_content.assert_called_once()

def test_generate_project_scaffold_retry_success(gemini_client):
    # First call fails, second succeeds
    mock_response_success = MagicMock()
    mock_response_success.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "echo success"
    })

    gemini_client.client.models.generate_content.side_effect = [
        Exception("API Error"),
        mock_response_success
    ]

    idea_data = {
        "title": "My App",
        "description": "App desc",
        "slug": "my-app",
        "tech_stack": [],
        "features": []
    }
    result = gemini_client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "echo success"
    assert gemini_client.client.models.generate_content.call_count == 2

def test_generate_project_scaffold_fallback(gemini_client):
    # All retries fail
    gemini_client.client.models.generate_content.side_effect = Exception("Persistent Error")

    idea_data = {
        "title": "Fallback App",
        "description": "Fallback desc",
        "slug": "fallback-app",
        "tech_stack": [],
        "features": []
    }

    # Patch logger to avoid cluttering output
    with patch('src.services.gemini.logger'):
        result = gemini_client.generate_project_scaffold(idea_data, max_retries=1)

    # Should return fallback scaffold which has "python main.py" as run command
    assert result["run_command"] == "python main.py"
    # Called: initial + 1 retry = 2 calls
    assert gemini_client.client.models.generate_content.call_count == 2
