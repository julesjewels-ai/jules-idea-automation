import pytest
import json
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError, ConfigurationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

def test_init_no_api_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ConfigurationError):
            GeminiClient(api_key=None)

def test_init_with_api_key(mock_genai_client):
    client = GeminiClient(api_key="test_key")
    assert client.api_key == "test_key"

def test_generate_idea(mock_genai_client):
    # Setup
    client = GeminiClient(api_key="test_key")
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Test Idea",
        "description": "Desc",
        "slug": "slug",
        "tech_stack": [],
        "features": []
    })
    client.client.models.generate_content.return_value = mock_response

    # Execute
    result = client.generate_idea(category="web_app")

    # Verify
    assert result["title"] == "Test Idea"
    client.client.models.generate_content.assert_called_once()

def test_extract_idea_from_text(mock_genai_client):
    # Setup
    client = GeminiClient(api_key="test_key")
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Extracted",
        "description": "Desc",
        "slug": "slug",
        "tech_stack": [],
        "features": []
    })
    client.client.models.generate_content.return_value = mock_response

    # Execute
    result = client.extract_idea_from_text("some text")

    # Verify
    assert result["title"] == "Extracted"
    client.client.models.generate_content.assert_called_once()

def test_generate_project_scaffold(mock_genai_client):
    # Setup
    client = GeminiClient(api_key="test_key")
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "cmd"
    })
    client.client.models.generate_content.return_value = mock_response

    idea_data = {"title": "Test", "description": "Desc", "slug": "slug", "tech_stack": [], "features": []}

    # Execute
    result = client.generate_project_scaffold(idea_data)

    # Verify
    assert result["run_command"] == "cmd"
    client.client.models.generate_content.assert_called_once()

def test_generate_error(mock_genai_client):
    # Setup
    client = GeminiClient(api_key="test_key")
    mock_response = MagicMock()
    mock_response.text = 'invalid json'
    client.client.models.generate_content.return_value = mock_response

    # Execute & Verify
    with pytest.raises(GenerationError):
        client.generate_idea()

def test_scaffold_retry_logic(mock_genai_client):
    # Setup
    client = GeminiClient(api_key="test_key")
    mock_response_success = MagicMock()
    mock_response_success.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "success"
    })

    # First call fails (raises Exception), second succeeds
    client.client.models.generate_content.side_effect = [Exception("Error"), mock_response_success]

    idea_data = {"title": "Test", "description": "Desc", "slug": "slug", "tech_stack": [], "features": []}

    # Execute
    result = client.generate_project_scaffold(idea_data, max_retries=1)

    # Verify
    assert result["run_command"] == "success"
    assert client.client.models.generate_content.call_count == 2
