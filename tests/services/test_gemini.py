import json
import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

def test_generate_idea_success(mock_genai_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Test App",
        "description": "A test application",
        "slug": "test-app",
        "tech_stack": ["Python"],
        "features": ["Feature 1"]
    })
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="fake_key")
    result = client.generate_idea()

    assert result["title"] == "Test App"
    assert result["description"] == "A test application"

def test_generate_idea_validation_error(mock_genai_client):
    # Setup mock response with missing required field 'title'
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "description": "A test application",
        "slug": "test-app",
        "tech_stack": ["Python"],
        "features": ["Feature 1"]
    })
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="fake_key")

    with pytest.raises(GenerationError) as excinfo:
        client.generate_idea()

    # Check main error message
    assert "Gemini response validation failed" in str(excinfo.value)
    assert "title" in str(excinfo.value)

    # Check if the tip provides helpful context
    assert "The model output did not match the required schema" in excinfo.value.tip

def test_extract_idea_from_text_validation_error(mock_genai_client):
    # Setup mock response with missing required field
    mock_response = MagicMock()
    mock_response.text = json.dumps({"description": "only description"})
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="fake_key")

    with pytest.raises(GenerationError) as excinfo:
        client.extract_idea_from_text("some text")

    assert "Gemini response validation failed" in str(excinfo.value)
    assert "title" in str(excinfo.value)

def test_generate_project_scaffold_validation_error(mock_genai_client):
    # Setup mock response with missing files field
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "requirements": ["pytest"],
        "run_command": "python main.py"
    })
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="fake_key")
    idea_data = {"title": "Test", "description": "Test", "slug": "test", "tech_stack": [], "features": []}

    # generate_project_scaffold retries on error, and if it fails all retries, it returns a fallback.
    # We want to ensure that validation error triggers the retry logic.
    # But since we mock the same response for all calls, it will eventually return the fallback.

    result = client.generate_project_scaffold(idea_data, max_retries=0)

    # It should catch GenerationError and return fallback scaffold
    assert result["files"][0]["path"] == "main.py"
    # Fallback scaffold is a dict, not pydantic model, so we check keys
    assert "files" in result
    assert "requirements" in result
