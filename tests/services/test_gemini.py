import json
import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as MockClient:
        client_instance = MockClient.return_value
        yield client_instance

@pytest.fixture
def gemini_client(mock_genai_client):
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"}):
        return GeminiClient()

def test_generate_idea_success(gemini_client, mock_genai_client):
    expected_response = {
        "title": "Test App",
        "description": "A test app description",
        "slug": "test-app",
        "tech_stack": ["python", "flask"],
        "features": ["feature1", "feature2"]
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(expected_response)
    mock_genai_client.models.generate_content.return_value = mock_response

    result = gemini_client.generate_idea(category="web_app")

    assert result == expected_response
    mock_genai_client.models.generate_content.assert_called_once()

def test_generate_idea_failure_json(gemini_client, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    mock_genai_client.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as exc:
        gemini_client.generate_idea()

    assert "Failed to parse Gemini response" in str(exc.value)

def test_extract_idea_from_text_success(gemini_client, mock_genai_client):
    expected_response = {
        "title": "Extracted App",
        "description": "Extracted description",
        "slug": "extracted-app",
        "tech_stack": ["react"],
        "features": ["analysis"]
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(expected_response)
    mock_genai_client.models.generate_content.return_value = mock_response

    result = gemini_client.extract_idea_from_text("Some text content")

    assert result == expected_response

def test_generate_project_scaffold_success(gemini_client, mock_genai_client):
    idea_data = {
        "title": "Test App",
        "description": "Desc",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }
    expected_scaffold = {
        "files": [{"path": "main.py", "content": "print('hello')", "description": "entry"}],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(expected_scaffold)
    mock_genai_client.models.generate_content.return_value = mock_response

    result = gemini_client.generate_project_scaffold(idea_data)

    assert result == expected_scaffold

def test_generate_project_scaffold_fallback(gemini_client, mock_genai_client):
    idea_data = {
        "title": "Test App",
        "description": "Desc",
        "slug": "test-app",
        "tech_stack": [],
        "features": []
    }

    # Simulate exception in generate_content
    mock_genai_client.models.generate_content.side_effect = Exception("API Error")

    result = gemini_client.generate_project_scaffold(idea_data, max_retries=1)

    # Check if fallback scaffold is returned
    assert "files" in result
    assert result["run_command"] == "python main.py"
    # Verify retries happened (initial + 1 retry = 2 calls)
    assert mock_genai_client.models.generate_content.call_count == 2
