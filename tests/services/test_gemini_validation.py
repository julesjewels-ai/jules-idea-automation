import pytest
from unittest.mock import Mock, patch
from pydantic import ValidationError
from src.services.gemini import GeminiClient
from src.core.models import TextContentInput, IdeaResponse

class TestGeminiValidation:
    @pytest.fixture
    def mock_env(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"}):
            yield

    @pytest.fixture
    def client(self, mock_env):
        with patch("src.services.gemini.genai.Client") as mock_genai:
            client = GeminiClient()
            yield client

    def test_text_content_input_validation(self):
        # Valid content
        valid = TextContentInput(content="Valid content string")
        assert valid.content == "Valid content string"

        # Too short
        with pytest.raises(ValidationError):
            TextContentInput(content="short")

    def test_extract_idea_sanitization(self, client):
        input_data = TextContentInput(content="<script>alert('xss')</script> Content")

        # Mock the generate_content response
        mock_response = Mock()
        mock_response.text = '{"title": "Test", "description": "Desc", "slug": "test", "tech_stack": [], "features": []}'
        client.client.models.generate_content.return_value = mock_response

        client.extract_idea_from_text(input_data)

        # Verify call arguments
        call_args = client.client.models.generate_content.call_args
        prompt = call_args.kwargs["contents"]

        # Check if input was escaped
        assert "&lt;script&gt;alert('xss')&lt;/script&gt;" in prompt
        assert "<script>" not in prompt
        # Check if wrapped in tags
        assert "<text_content>" in prompt
        assert "</text_content>" in prompt

    def test_generate_scaffold_sanitization(self, client):
        idea_data = {
            "title": "My <bold>Project</bold>",
            "description": "Desc with \"quotes\"",
            "slug": "slug",
            "tech_stack": [],
            "features": []
        }

        mock_response = Mock()
        mock_response.text = '{"files": [], "requirements": [], "run_command": ""}'
        client.client.models.generate_content.return_value = mock_response

        client.generate_project_scaffold(idea_data)

        call_args = client.client.models.generate_content.call_args
        prompt = call_args.kwargs["contents"]

        assert "My &lt;bold&gt;Project&lt;/bold&gt;" in prompt
        assert "<project_title>" in prompt
