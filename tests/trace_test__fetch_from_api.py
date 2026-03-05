import pytest
from pytest_mock import MockerFixture
from typing import Any, Callable, Type
from unittest.mock import MagicMock
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError
from google.genai import errors


class DummyAPIError(errors.APIError):  # type: ignore[misc]
    """Dummy exception for tests to bypass type checker issues with external libraries."""
    def __init__(self, message: str) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": {"message": message}}
        mock_resp.status_code = 503 if "503" in message else 400
        super().__init__(message, mock_resp)


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "prompt": "Test prompt",
        "schema": dict,
        "error_tip": "Fallback tip",
        "cache_key": "test_key",
    }


@pytest.fixture
def gemini_client(mocker: MockerFixture) -> GeminiClient:
    # Patch the genai.Client instantiation to return a mock client
    mock_genai_client_class = mocker.patch("src.services.gemini.genai.Client", autospec=True)
    mock_client_instance = MagicMock()
    mock_genai_client_class.return_value = mock_client_instance
    return GeminiClient(api_key="test_key")


@pytest.mark.parametrize(
    "setup_mock_behavior, expected",
    [
        # Happy Path: model succeeds
        (
            lambda mock_gen_content: setattr(mock_gen_content.return_value, "text", '{"result": "success"}'),
            {"result": "success"},
        ),
        # Edge Case: 503 error on first model, success on second
        (
            lambda mock_gen_content: setattr(mock_gen_content, "side_effect", [DummyAPIError("503 UNAVAILABLE"), MagicMock(text='{"result": "fallback"}')]),
            {"result": "fallback"},
        ),
        # Error State: all models fail
        (
            lambda mock_gen_content: setattr(mock_gen_content, "side_effect", [DummyAPIError("400 Bad Request")]),
            GenerationError,
        ),
    ],
)
def test_fetch_from_api_behavior(
    gemini_client: GeminiClient,
    mock_context: dict[str, Any],
    setup_mock_behavior: Callable[[MagicMock], None],
    expected: dict[str, Any] | Type[Exception],
) -> None:
    # Setup specific behavior for generate_content
    mock_generate_content: MagicMock = gemini_client.client.models.generate_content
    setup_mock_behavior(mock_generate_content)

    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            gemini_client._fetch_from_api(**mock_context)
        # Verify it attempted to call the API
        mock_generate_content.assert_called()
    else:
        result = gemini_client._fetch_from_api(**mock_context)
        assert result == expected
        mock_generate_content.assert_called()
