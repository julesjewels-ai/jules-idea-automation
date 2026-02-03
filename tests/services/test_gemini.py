import os
import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini import GeminiClient


@pytest.fixture
def mock_genai_client():
    with patch("src.services.gemini.genai.Client") as MockClient:
        # Create a mock instance
        mock_instance = MagicMock()
        # Return the mock instance when Client() is called
        MockClient.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def client(mock_genai_client):
    # Set the environment variable to avoid ConfigurationError
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
        return GeminiClient()


def test_extract_idea_from_text_prompt_construction(client, mock_genai_client):
    """Verify that the prompt wraps input in XML tags and escapes it."""
    # Define a mock response
    mock_response = MagicMock()
    mock_response.text = (
        '{"title": "Test Idea", "description": "Desc", '
        '"slug": "slug", "tech_stack": [], "features": []}'
    )
    mock_genai_client.models.generate_content.return_value = mock_response

    input_text = "Potentially <Malicious> Text & Stuff"
    client.extract_idea_from_text(input_text)

    # Check what was passed to generate_content
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args is not None

    args, kwargs = call_args
    prompt = kwargs.get('contents')

    assert prompt is not None
    assert "<text_content>" in prompt
    assert "</text_content>" in prompt
    assert "Potentially &lt;Malicious&gt; Text &amp; Stuff" in prompt
    assert "<Malicious>" not in prompt  # Should be escaped


def test_generate_project_scaffold_prompt_construction(
    client, mock_genai_client
):
    """Verify that the prompt wraps input in XML tags and escapes it."""
    mock_response = MagicMock()
    mock_response.text = (
        '{"files": [], "requirements": [], "run_command": "ls"}'
    )
    mock_genai_client.models.generate_content.return_value = mock_response

    idea_data = {
        "title": "Malicious <Title>",
        "description": "Malicious <Description>",
        "slug": "slug",
        "tech_stack": [],
        "features": []
    }

    client.generate_project_scaffold(idea_data)

    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args is not None
    args, kwargs = call_args
    prompt = kwargs.get('contents')

    assert prompt is not None
    assert "<project_title>" in prompt
    assert "</project_title>" in prompt
    assert "<project_description>" in prompt
    assert "Malicious &lt;Title&gt;" in prompt
    assert "Malicious &lt;Description&gt;" in prompt
