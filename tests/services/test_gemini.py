import pytest
from unittest.mock import MagicMock, patch
import json
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

@pytest.fixture
def mock_genai_client():
    with patch('src.services.gemini.genai.Client') as mock:
        yield mock

@pytest.fixture
def gemini_client(mock_genai_client):
    with patch('os.environ.get', return_value='fake_key'):
        client = GeminiClient(api_key="fake_key")
    return client

def test_generate_idea_success(gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Test Idea",
        "description": "A test idea description",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    })
    gemini_client.client.models.generate_content.return_value = mock_response

    idea = gemini_client.generate_idea()

    assert idea["title"] == "Test Idea"
    gemini_client.client.models.generate_content.assert_called_once()

def test_generate_idea_json_error(gemini_client):
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    gemini_client.client.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError):
        gemini_client.generate_idea()

def test_extract_idea_from_text_success(gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Extracted Idea",
        "description": "Extracted description",
        "slug": "extracted-idea",
        "tech_stack": ["js"],
        "features": ["f1"]
    })
    gemini_client.client.models.generate_content.return_value = mock_response

    idea = gemini_client.extract_idea_from_text("some text")

    assert idea["title"] == "Extracted Idea"

def test_generate_project_scaffold_success(gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "echo hello"
    })
    gemini_client.client.models.generate_content.return_value = mock_response

    data = {
        "title": "T", "description": "D", "slug": "s", "tech_stack": [], "features": []
    }
    scaffold = gemini_client.generate_project_scaffold(data)

    assert scaffold["run_command"] == "echo hello"

def test_generate_project_scaffold_retry_logic(gemini_client):
    mock_response_success = MagicMock()
    mock_response_success.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "success"
    })

    # First call raises Exception, second succeeds
    gemini_client.client.models.generate_content.side_effect = [Exception("Fail"), mock_response_success]

    data = {
        "title": "T", "description": "D", "slug": "s", "tech_stack": [], "features": []
    }
    scaffold = gemini_client.generate_project_scaffold(data, max_retries=1)

    assert scaffold["run_command"] == "success"
    assert gemini_client.client.models.generate_content.call_count == 2

def test_generate_project_scaffold_fallback(gemini_client):
    # Always fail
    gemini_client.client.models.generate_content.side_effect = Exception("Fail")

    data = {
        "title": "T", "description": "D", "slug": "s", "tech_stack": [], "features": []
    }
    scaffold = gemini_client.generate_project_scaffold(data, max_retries=1)

    # Should return fallback which has python main.py
    assert scaffold["run_command"] == "python main.py"
