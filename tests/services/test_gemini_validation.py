import pytest
import json
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

class MockResponse:
    def __init__(self, text):
        self.text = text

@pytest.fixture
def mock_genai_client():
    with patch('src.services.gemini.genai.Client') as mock:
        yield mock

def test_generate_idea_validation_error(mock_genai_client):
    """
    Verifies that GenerationError is raised when the response schema is invalid.
    """
    # Missing 'description' which is required by IdeaResponse
    invalid_json = json.dumps({"title": "Test Idea", "slug": "test-idea"})

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = MockResponse(invalid_json)

    client = GeminiClient(api_key="fake_key")

    with pytest.raises(GenerationError) as exc_info:
        client.generate_idea()

    # Verify the tip contains validation details
    # We expect something like: "• Field 'description': Field required"
    assert exc_info.value.tip is not None
    assert "description" in exc_info.value.tip

def test_generate_idea_validation_error_structure(mock_genai_client):
    """
    Verifies that GenerationError is raised when the response structure is invalid (e.g. list instead of dict),
    and that it handles the empty 'loc' gracefully without crashing.
    """
    # Invalid structure: List instead of Dict
    invalid_json = json.dumps([{"title": "Test Idea"}])

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = MockResponse(invalid_json)

    client = GeminiClient(api_key="fake_key")

    with pytest.raises(GenerationError) as exc_info:
        client.generate_idea()

    # Verify the tip contains "Structure" (our fallback for empty loc)
    # The error message from pydantic for list instead of dict usually says "Input should be a valid dictionary..."
    assert exc_info.value.tip is not None
    assert "Structure" in exc_info.value.tip
