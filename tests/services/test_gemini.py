import pytest
from unittest.mock import MagicMock, patch
import json
import os
from google.genai import errors
from src.services.gemini import GeminiClient
from src.utils.errors import ConfigurationError, GenerationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture
def client(mock_genai_client):
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        return GeminiClient()

def test_init_raises_error_without_api_key():
    # Ensure environment is clean
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError):
            GeminiClient(api_key=None)

def test_init_with_env_var():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        client = GeminiClient()
        assert client.api_key == "test_key"

def test_generate_idea_success(client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Test App",
        "description": "A test app",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["feature1"]
    })
    client.client.models.generate_content.return_value = mock_response

    result = client.generate_idea(category="web_app")

    assert result["title"] == "Test App"
    client.client.models.generate_content.assert_called_once()

def test_generate_idea_json_error(client):
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    client.client.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError):
        client.generate_idea()

def test_generate_idea_api_error(client):
    # Simulate an API error (e.g., invalid key)
    error = errors.ClientError(
        code=400,
        response_json={"message": "API key not valid"}
    )
    client.client.models.generate_content.side_effect = error

    with pytest.raises(GenerationError) as excinfo:
        client.generate_idea()

    assert "Gemini API Error" in str(excinfo.value)
    assert "Your GEMINI_API_KEY seems invalid" in excinfo.value.tip

def test_extract_idea_from_text_success(client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Extracted App",
        "description": "An extracted app",
        "slug": "extracted-app",
        "tech_stack": ["python"],
        "features": ["feature1"]
    })
    client.client.models.generate_content.return_value = mock_response

    result = client.extract_idea_from_text("some long text content")

    assert result["title"] == "Extracted App"
    client.client.models.generate_content.assert_called_once()

def test_generate_project_scaffold_success(client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "files": [],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    })
    client.client.models.generate_content.return_value = mock_response

    idea_data = {
        "title": "Test App",
        "description": "Desc",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }
    result = client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "python main.py"

def test_generate_project_scaffold_retry_then_success(client):
    # First call raises exception, second call succeeds
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "python main.py"
    })

    client.client.models.generate_content.side_effect = [
        Exception("API Error"),
        mock_response
    ]

    idea_data = {"title": "Test", "description": "Desc"}
    result = client.generate_project_scaffold(idea_data)

    assert result["run_command"] == "python main.py"
    assert client.client.models.generate_content.call_count == 2

def test_generate_project_scaffold_fallback(client):
    # All calls fail
    client.client.models.generate_content.side_effect = Exception("API Error")

    idea_data = {"title": "Test App", "description": "Desc"}
    # max_retries=1 means attempts: 0 (initial), 1 (retry 1). Total 2.
    result = client.generate_project_scaffold(idea_data, max_retries=1)

    # Check for fallback structure
    assert result["run_command"] == "python main.py"
    assert any(f["path"] == "main.py" for f in result["files"])
    assert client.client.models.generate_content.call_count == 2
