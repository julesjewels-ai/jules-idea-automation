import pytest
import json
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError
from src.core.models import IdeaResponse

@pytest.fixture
def mock_genai_client():
    with patch('src.services.gemini.genai.Client') as mock:
        yield mock

@pytest.fixture
def client(mock_genai_client):
    # Setup mock client instance
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
    client.client.models.generate_content.return_value = mock_response

    # Execute
    result = client.generate_idea(category="web_app")

    # Verify
    assert result == expected_data
    client.client.models.generate_content.assert_called_once()

    # Verify arguments
    _, kwargs = client.client.models.generate_content.call_args
    assert "Generate a creative web application idea" in kwargs['contents']
    assert kwargs['config'].response_schema == IdeaResponse

def test_generate_idea_failure(client):
    # Setup mock failure (invalid JSON)
    mock_response = MagicMock()
    mock_response.text = "Invalid JSON"
    client.client.models.generate_content.return_value = mock_response

    # Execute & Verify
    with pytest.raises(GenerationError) as excinfo:
        client.generate_idea()

    assert "Failed to parse Gemini response" in str(excinfo.value)
    assert "The AI model returned invalid JSON" in excinfo.value.tip

def test_extract_idea_from_text_success(client):
    # Setup
    mock_response = MagicMock()
    expected_data = {"title": "Extracted Idea", "description": "...", "slug": "extracted", "tech_stack": [], "features": []}
    mock_response.text = json.dumps(expected_data)
    client.client.models.generate_content.return_value = mock_response

    # Execute
    result = client.extract_idea_from_text("some text content")

    # Verify
    assert result == expected_data

    # Verify arguments
    _, kwargs = client.client.models.generate_content.call_args
    assert "Analyze the following text" in kwargs['contents']
    assert "some text content" in kwargs['contents']

def test_extract_idea_from_text_failure(client):
    # Setup
    mock_response = MagicMock()
    mock_response.text = "Not JSON"
    client.client.models.generate_content.return_value = mock_response

    # Execute & Verify
    with pytest.raises(GenerationError) as excinfo:
        client.extract_idea_from_text("content")

    assert "Failed to parse Gemini response" in str(excinfo.value)
    assert "while analyzing the website content" in excinfo.value.tip
