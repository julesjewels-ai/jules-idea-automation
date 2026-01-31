"""Tests for GeminiClient prompt injection and validation."""

import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient
from src.core.models import TextContentInput

class TestGeminiPromptInjection:

    @pytest.fixture
    def gemini_client(self):
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            client = GeminiClient()
            # Mock the internal google client
            client.client = MagicMock()
            return client

    def test_extract_idea_sanitizes_input(self, gemini_client):
        """Test that input text is sanitized and wrapped in tags."""
        # Use content that meets min_length=10 requirement
        malicious_input = 'Valid length text with <script>alert(1)</script> and "quotes"'
        expected_escaped = 'Valid length text with &lt;script&gt;alert(1)&lt;/script&gt; and "quotes"'

        text_input = TextContentInput(content=malicious_input)

        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"title": "Test", "description": "Desc", "slug": "test", "tech_stack": [], "features": []}'
        gemini_client.client.models.generate_content.return_value = mock_response

        gemini_client.extract_idea_from_text(text_input)

        # Verify the prompt construction
        call_args = gemini_client.client.models.generate_content.call_args
        assert call_args is not None

        prompt_content = call_args.kwargs['contents']

        # Check for XML tags
        assert '<text_content>' in prompt_content
        assert '</text_content>' in prompt_content

        # Check that content is escaped
        assert expected_escaped in prompt_content
        assert '<script>' not in prompt_content

    def test_extract_idea_handles_validation_error(self):
        """Test that Pydantic validation catches invalid inputs."""
        # Too short
        with pytest.raises(ValueError):
            TextContentInput(content="Short")

        # Too long
        long_text = "a" * 100001
        with pytest.raises(ValueError):
            TextContentInput(content=long_text)
