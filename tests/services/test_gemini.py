import json
import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import ConfigurationError, GenerationError
from src.core.models import IdeaResponse, ProjectScaffold

@patch("src.services.gemini.genai")
@patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
def test_init_success(mock_genai):
    client = GeminiClient()
    assert client.api_key == "test-key"
    mock_genai.Client.assert_called_once()

@patch.dict("os.environ", {}, clear=True)
def test_init_no_api_key():
    with pytest.raises(ConfigurationError):
        GeminiClient()

@patch("src.services.gemini.genai")
@patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
def test_generate_idea_success(mock_genai):
    client = GeminiClient()

    mock_response = MagicMock()
    mock_response.text = '{"title": "Test App", "description": "Desc", "slug": "test-app", "tech_stack": [], "features": []}'
    client.client.models.generate_content.return_value = mock_response

    result = client.generate_idea()

    assert result["title"] == "Test App"
    client.client.models.generate_content.assert_called_once()

@patch("src.services.gemini.genai")
@patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
def test_generate_idea_json_error(mock_genai):
    client = GeminiClient()

    mock_response = MagicMock()
    mock_response.text = 'Invalid JSON'
    client.client.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as exc:
        client.generate_idea()

    assert "Failed to parse Gemini response" in str(exc.value)

@patch("src.services.gemini.genai")
@patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
def test_extract_idea_from_text_success(mock_genai):
    client = GeminiClient()

    mock_response = MagicMock()
    mock_response.text = '{"title": "Extracted App", "description": "Desc", "slug": "extracted-app", "tech_stack": [], "features": []}'
    client.client.models.generate_content.return_value = mock_response

    result = client.extract_idea_from_text("Some text content")

    assert result["title"] == "Extracted App"
    client.client.models.generate_content.assert_called_once()

@patch("src.services.gemini.genai")
@patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
def test_generate_project_scaffold_success(mock_genai):
    client = GeminiClient()

    mock_response = MagicMock()
    mock_response.text = '{"files": [], "requirements": [], "run_command": "python main.py"}'
    client.client.models.generate_content.return_value = mock_response

    idea_data = {"title": "Test", "description": "Desc", "slug": "test", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "python main.py"
    client.client.models.generate_content.assert_called_once()

@patch("src.services.gemini.genai")
@patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
def test_generate_project_scaffold_fallback(mock_genai):
    client = GeminiClient()

    # Mock exception on generate_content to trigger fallback
    client.client.models.generate_content.side_effect = Exception("API Error")

    idea_data = {"title": "Test", "description": "Desc", "slug": "test", "tech_stack": [], "features": []}
    result = client.generate_project_scaffold(idea_data, max_retries=0)

    assert result["run_command"] == "python main.py"
    # Ensure fallback files are present
    file_paths = [f["path"] for f in result["files"]]
    assert "main.py" in file_paths
    assert "Makefile" in file_paths
