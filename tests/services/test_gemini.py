import pytest
from unittest.mock import MagicMock, patch
import json
from src.services.gemini import GeminiClient, GenerationError
from src.core.models import IdeaResponse, ProjectScaffold

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture
def client(mock_genai_client):
    return GeminiClient(api_key="test-key")

def test_generate_idea_success(client, mock_genai_client):
    # Setup mock response
    mock_response = MagicMock()
    expected_data = {
        "title": "Test App",
        "description": "A test app",
        "slug": "test-app",
        "tech_stack": ["Python"],
        "features": ["Feature 1"]
    }
    mock_response.text = json.dumps(expected_data)

    # Configure the mock instance returned by Client()
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    # Call method
    result = client.generate_idea(category="web_app")

    # Verify
    assert result == expected_data
    mock_instance.models.generate_content.assert_called_once()

    # Check arguments
    call_kwargs = mock_instance.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-3-pro-preview"
    assert "Include recommended tech stack" in call_kwargs["contents"]

def test_generate_idea_json_error(client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = "Invalid JSON"

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError, match="Failed to parse Gemini response"):
        client.generate_idea()

def test_extract_idea_from_text_success(client, mock_genai_client):
    mock_response = MagicMock()
    expected_data = {"title": "Extracted Idea", "description": "Desc", "slug": "extracted", "tech_stack": [], "features": []}
    mock_response.text = json.dumps(expected_data)

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    result = client.extract_idea_from_text("Some text content")

    assert result == expected_data
    mock_instance.models.generate_content.assert_called_once()
    assert "Analyze the following text" in mock_instance.models.generate_content.call_args.kwargs["contents"]

def test_generate_project_scaffold_success(client, mock_genai_client):
    mock_response = MagicMock()
    expected_data = {
        "files": [{"path": "main.py", "content": "print('hello')", "description": "entry"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
    mock_response.text = json.dumps(expected_data)

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    idea_data = {"title": "Test", "description": "Test", "slug": "test", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data)

    assert result == expected_data

def test_generate_project_scaffold_retry_then_fallback(client, mock_genai_client):
    # Simulate exception then failure
    mock_instance = mock_genai_client.return_value
    # First call raises Exception
    # Second call raises Exception (max_retries=1)
    # So it should return fallback

    mock_instance.models.generate_content.side_effect = Exception("API Error")

    idea_data = {"title": "Fallback", "description": "Fallback Desc", "slug": "fallback", "tech_stack": [], "features": []}

    result = client.generate_project_scaffold(idea_data, max_retries=1)

    # Verify fallback structure
    assert "files" in result
    assert result["run_command"] == "python main.py"
    assert mock_instance.models.generate_content.call_count == 2 # Initial + 1 retry
