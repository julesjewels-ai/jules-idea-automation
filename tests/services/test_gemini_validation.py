import pytest
from unittest.mock import MagicMock, patch
import json
import os
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

@pytest.fixture
def client(mock_genai_client):
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        return GeminiClient()

def test_generate_idea_pydantic_validation_error(client):
    """Test that missing fields in the response raise GenerationError with helpful tip."""
    mock_response = MagicMock()
    # Missing 'slug' which is required
    mock_response.text = json.dumps({
        "title": "Test App",
        "description": "A test app"
    })
    client.client.models.generate_content.return_value = mock_response

    with pytest.raises(GenerationError) as excinfo:
        client.generate_idea(category="web_app")

    # Check that the tip contains helpful info
    tip = excinfo.value.tip
    assert "slug" in tip
    assert "Field required" in tip
    # Check for bullet point format
    assert "* Field 'slug'" in tip or "• Field 'slug'" in tip or "- Field 'slug'" in tip

if __name__ == "__main__":
    pass
