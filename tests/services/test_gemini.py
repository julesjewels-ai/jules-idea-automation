
import pytest
import json
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as mock:
        yield mock

class TestGeminiClient:
    def test_generate_idea_validation_error(self, mock_genai_client):
        """Test that generate_idea raises GenerationError on invalid schema."""
        client = GeminiClient(api_key="test_key")

        # Mock response with missing 'title'
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "description": "A cool app",
            "slug": "cool-app",
            "tech_stack": ["python"],
            "features": ["login"]
        })

        mock_client_instance = mock_genai_client.return_value
        mock_client_instance.models.generate_content.return_value = mock_response

        with pytest.raises(GenerationError) as excinfo:
            client.generate_idea()

        assert "The AI model returned invalid data" in excinfo.value.tip
        assert "title" in excinfo.value.tip
        assert "Field required" in excinfo.value.tip

    def test_extract_idea_validation_error(self, mock_genai_client):
        """Test that extract_idea_from_text raises GenerationError on invalid schema."""
        client = GeminiClient(api_key="test_key")

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "title": "A cool app"
            # Missing description, etc.
        })

        mock_client_instance = mock_genai_client.return_value
        mock_client_instance.models.generate_content.return_value = mock_response

        with pytest.raises(GenerationError) as excinfo:
            client.extract_idea_from_text("some text")

        assert "The AI model returned invalid data" in excinfo.value.tip
        assert "description" in excinfo.value.tip

    def test_generate_project_scaffold_validation_retry(self, mock_genai_client):
        """Test that generate_project_scaffold retries on validation error."""
        client = GeminiClient(api_key="test_key")

        # Mock responses: 1st attempt invalid, 2nd attempt valid
        mock_response_invalid = MagicMock()
        mock_response_invalid.text = json.dumps({}) # Missing files (required)

        mock_response_valid = MagicMock()
        mock_response_valid.text = json.dumps({
            "files": [],
            "requirements": ["pytest"],
            "run_command": "python main.py"
        })

        mock_client_instance = mock_genai_client.return_value
        mock_client_instance.models.generate_content.side_effect = [
            mock_response_invalid,
            mock_response_valid
        ]

        result = client.generate_project_scaffold({"title": "Test", "description": "Test"}, max_retries=1)

        assert result["run_command"] == "python main.py"
        assert mock_client_instance.models.generate_content.call_count == 2
