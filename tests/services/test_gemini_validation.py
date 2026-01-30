import pytest
import os
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from src.core.models import TextContentInput
from src.services.gemini import GeminiClient

def test_text_content_input_valid():
    """Test valid text content input."""
    input_model = TextContentInput(content="This is a valid text content that is long enough.")
    assert input_model.content == "This is a valid text content that is long enough."

def test_text_content_input_too_short():
    """Test text content input that is too short."""
    with pytest.raises(ValidationError):
        TextContentInput(content="Short")

def test_text_content_input_too_long():
    """Test text content input that is too long."""
    long_text = "a" * 100001
    with pytest.raises(ValidationError):
        TextContentInput(content=long_text)

@patch("src.services.gemini.genai.Client")
@patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
def test_extract_idea_from_text_prompt_structure(mock_genai_client_cls):
    """Test that extract_idea_from_text constructs the prompt correctly with XML tags."""
    # Setup mock
    mock_client = MagicMock()
    mock_genai_client_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = '{"title": "Test Idea", "description": "Test Desc", "slug": "test", "tech_stack": [], "features": []}'
    mock_client.models.generate_content.return_value = mock_response

    gemini = GeminiClient()
    text_input = TextContentInput(content="Test content for prompt injection check.")

    gemini.extract_idea_from_text(text_input)

    # Verify call arguments
    call_args = mock_client.models.generate_content.call_args
    assert call_args is not None

    # Check contents (prompt)
    prompt = call_args.kwargs['contents']
    assert "<text_content>" in prompt
    assert "</text_content>" in prompt
    assert "Test content for prompt injection check." in prompt

    # Check escaping (simple check)
    gemini.extract_idea_from_text(TextContentInput(content="<script>alert('xss')</script>"))
    prompt_escaped = mock_client.models.generate_content.call_args.kwargs['contents']
    assert "&lt;script&gt;alert('xss')&lt;/script&gt;" in prompt_escaped
