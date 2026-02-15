import pytest
from pytest_mock import MockerFixture
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError
from google.genai import errors
import os

# Define a mock error class that behaves like google.genai.errors.APIError
# We override __str__ because that's what _map_api_error uses.
class MockAPIError(errors.APIError):
    def __init__(self, message: str):
        self.message = message
        # We intentionally do not call super().__init__ to avoid needing
        # to mock the specific arguments required by the real APIError class.
        # This is safe because _map_api_error only uses str(e).

    def __str__(self) -> str:
        return self.message

@pytest.fixture
def mock_gemini_client(mocker: MockerFixture) -> GeminiClient:
    """Creates a GeminiClient instance with mocked dependencies."""
    # Patch the genai.Client to avoid network calls during initialization
    mocker.patch("src.services.gemini.genai.Client")

    # Set the API key environment variable to pass the __init__ check
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})

    return GeminiClient()

@pytest.mark.parametrize("error_message, expected_tip", [
    # Happy Path / Known Errors
    ("400 API key not valid", "Your GEMINI_API_KEY seems invalid. Check your .env file."),
    ("Some other 400 error", "Your GEMINI_API_KEY seems invalid. Check your .env file."),
    ("429 Too Many Requests", "You have exceeded your API quota. Try again later."),
    ("Quota exceeded for this project", "You have exceeded your API quota. Try again later."),
    ("403 Forbidden", "You don't have permission to access this model."),

    # Edge Case / Unknown Errors
    ("500 Internal Server Error", "Check your internet connection and API status."),
    ("Network timeout", "Check your internet connection and API status."),
    ("", "Check your internet connection and API status."), # Empty message
])
def test_map_api_error_behavior(
    mock_gemini_client: GeminiClient,
    error_message: str,
    expected_tip: str
) -> None:
    # 1. Setup
    # Create an instance of our mock error with the parameterized message
    api_error = MockAPIError(error_message)

    # 2. Execution
    result_error = mock_gemini_client._map_api_error(api_error)

    # 3. Validation
    assert isinstance(result_error, GenerationError)
    assert result_error.tip == expected_tip
    assert error_message in str(result_error)
