import json
import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError, ConfigurationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture
def gemini_client(mock_genai_client):
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        client = GeminiClient()
        return client

def test_init_raises_error_without_api_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ConfigurationError):
            GeminiClient()

def test_generate_idea_success(gemini_client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = '{"title": "Test Idea", "description": "A test idea"}'

    # Mock the return value of generate_content
    # Note: access pattern is client.models.generate_content
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    result = gemini_client.generate_idea(category="web_app")

    assert result == {"title": "Test Idea", "description": "A test idea"}
    mock_genai_client.return_value.models.generate_content.assert_called_once()

def test_generate_idea_json_error(gemini_client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = 'Invalid JSON'
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as excinfo:
        gemini_client.generate_idea()

    assert "Failed to parse Gemini response" in str(excinfo.value)
    assert "The AI model returned invalid JSON" in excinfo.value.tip

def test_extract_idea_from_text_success(gemini_client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = '{"title": "Extracted Idea", "description": "Extracted"}'
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    result = gemini_client.extract_idea_from_text("Some text content")

    assert result == {"title": "Extracted Idea", "description": "Extracted"}

def test_extract_idea_from_text_json_error(gemini_client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = 'Invalid JSON'
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as excinfo:
        gemini_client.extract_idea_from_text("content")

    assert "Failed to parse Gemini response" in str(excinfo.value)
    assert "while analyzing the website content" in excinfo.value.tip

def test_generate_project_scaffold_success(gemini_client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = '{"files": [], "requirements": [], "run_command": "python main.py"}'
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    idea_data = {"title": "Test", "description": "Desc", "slug": "test", "tech_stack": [], "features": []}
    result = gemini_client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "python main.py"

def test_generate_project_scaffold_retry_success(gemini_client, mock_genai_client):
    # First call fails, second succeeds
    fail_response = MagicMock()
    fail_response.text = 'Invalid JSON'

    success_response = MagicMock()
    success_response.text = '{"files": [], "requirements": [], "run_command": "success"}'

    # We need to simulate the exception raised by json.loads
    # Or simulate generate_content raising an exception.
    # The code catches Exception, so let's mock generate_content to return bad json first, then good json.

    # Wait, existing code does:
    # try:
    #    response = ...
    #    return json.loads(response.text)
    # except Exception as e: ...

    # So if we return bad text, json.loads raises JSONDecodeError, which is caught.

    mock_genai_client.return_value.models.generate_content.side_effect = [
        Exception("API Error"), # First attempt fails
        success_response        # Second attempt succeeds
    ]

    idea_data = {"title": "Test", "description": "Desc", "slug": "test", "tech_stack": [], "features": []}
    result = gemini_client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "success"
    assert mock_genai_client.return_value.models.generate_content.call_count == 2

def test_generate_project_scaffold_fallback(gemini_client, mock_genai_client):
    # All retries fail
    mock_genai_client.return_value.models.generate_content.side_effect = Exception("Persistent Failure")

    idea_data = {"title": "Fallback Test", "description": "Desc", "slug": "fallback", "tech_stack": [], "features": []}

    # Should verify log error call? Optional.

    result = gemini_client.generate_project_scaffold(idea_data, max_retries=1)

    # Check if we got the fallback scaffold
    assert "files" in result
    # Check for a known file in fallback
    file_paths = [f["path"] for f in result["files"]]
    assert "main.py" in file_paths
    assert result["run_command"] == "python main.py"
