import pytest
from unittest.mock import MagicMock, patch
import json
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError

@patch('src.services.gemini.genai.Client')
def test_extract_idea_from_text_calls_api_securely(mock_genai_client_class):
    # Setup
    mock_client_instance = mock_genai_client_class.return_value
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Test Idea",
        "description": "A test idea description",
        "slug": "test-idea",
        "tech_stack": ["python"],
        "features": ["feature1"]
    })
    mock_client_instance.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="fake-key")
    # Input with special characters that need escaping
    text_content = "This is a <script>alert('hack')</script> website."

    # Execute
    result = client.extract_idea_from_text(text_content)

    # Verify
    assert result["title"] == "Test Idea"
    mock_client_instance.models.generate_content.assert_called_once()

    # Check arguments
    call_args = mock_client_instance.models.generate_content.call_args
    assert call_args is not None
    _, kwargs = call_args
    prompt = kwargs.get('contents', '')

    # Verify secure prompting
    assert "<text_content>" in prompt
    assert "</text_content>" in prompt
    assert "&lt;script&gt;" in prompt # Escaped input
    assert "<script>" not in prompt # Raw input should not be there

@patch('src.services.gemini.genai.Client')
def test_extract_idea_from_text_validation_error(mock_genai_client_class):
    client = GeminiClient(api_key="fake-key")
    short_text = "Too short" # Less than 10 chars

    # It seems my implementation truncates instead of raising, or wraps it.
    # Let's check my implementation:
    # try: validated_input = TextContentInput(text=text) ...
    # except Exception as e: ... truncated_text = text[:100000] ... validated_input = TextContentInput(text=truncated_text)

    # If I pass "Too short", TextContentInput will fail min_length=10.
    # The except block will try again with same text (truncated is same).
    # It will raise validation error again.

    with pytest.raises(Exception): # Pydantic ValidationError
        client.extract_idea_from_text(short_text)

@patch('src.services.gemini.genai.Client')
def test_generate_project_scaffold_calls_api_securely(mock_genai_client_class):
    # Setup
    mock_client_instance = mock_genai_client_class.return_value
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "files": [],
        "requirements": [],
        "run_command": "python main.py"
    })
    mock_client_instance.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="fake-key")
    idea_data = {
        "title": "My <App>",
        "description": "A description",
        "slug": "my-app",
        "tech_stack": [],
        "features": []
    }

    # Execute
    client.generate_project_scaffold(idea_data)

    # Verify
    mock_client_instance.models.generate_content.assert_called_once()

    # Check arguments
    call_args = mock_client_instance.models.generate_content.call_args
    _, kwargs = call_args
    prompt = kwargs.get('contents', '')

    # Verify title/description are in prompt and escaped
    assert "My &lt;App&gt;" in prompt
    assert "<project_details>" in prompt
