from typing import Any
from unittest.mock import MagicMock

import pytest
from google.genai.errors import APIError
from pytest_mock import MockerFixture

from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError


class MockAPIError(APIError):  # type: ignore[misc]
    """Mock APIError for testing."""

    def __init__(self, message: str, code: int = 503):
        # We must support google.genai 0.8.0 signature, but also handle whatever CI uses.
        # So we just pass positional to Exception and patch __str__.
        super(APIError, self).__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return self.message


@pytest.fixture
def gemini_client() -> GeminiClient:
    return GeminiClient(api_key="test_key")


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "prompt": "generate a test idea",
        "schema": dict,
        "error_tip": "test error tip",
        "cache_key": "test_cache_key",
    }


@pytest.fixture
def setup_happy_path() -> tuple[MagicMock | list[MagicMock | Exception] | Exception, dict[str, str]]:
    mock_response = MagicMock()
    mock_response.text = '{"idea": "valid"}'
    return (mock_response, {"idea": "valid"})


@pytest.fixture
def setup_fallback_edge_case() -> tuple[MagicMock | list[MagicMock | Exception] | Exception, dict[str, str]]:
    mock_error = MockAPIError(message="503 UNAVAILABLE", code=503)
    mock_response = MagicMock()
    mock_response.text = '{"idea": "fallback_valid"}'
    return ([mock_error, mock_response], {"idea": "fallback_valid"})


@pytest.fixture
def setup_error_state() -> tuple[MagicMock | list[MagicMock | Exception] | Exception, dict[str, str]]:
    mock_error = MockAPIError(message="503 UNAVAILABLE", code=503)
    return (mock_error, {})


@pytest.mark.parametrize(
    "mock_setup_fixture, expected_call_count, expected",
    [
        ("setup_happy_path", 1, {"idea": "valid"}),
        ("setup_fallback_edge_case", 2, {"idea": "fallback_valid"}),
        ("setup_error_state", 2, GenerationError),
    ],
)
def test_fetch_from_api_behavior(
    mocker: MockerFixture,
    gemini_client: GeminiClient,
    mock_context: dict[str, Any],
    request: pytest.FixtureRequest,
    mock_setup_fixture: str,
    expected_call_count: int,
    expected: dict[str, str] | type[Exception],
) -> None:
    # Get the setup data from the fixture
    # Note: We deliberately let the real `_process_api_response` run to provide a true
    # high-fidelity test of how _fetch_from_api orchestrates API responses.
    mock_side_effect_or_return_value, mock_process_return = request.getfixturevalue(mock_setup_fixture)

    # 1. Setup Mocks (Namespace Verified)
    mock_generate_content = mocker.patch.object(gemini_client.client.models, "generate_content", autospec=True)

    if isinstance(mock_side_effect_or_return_value, Exception) or isinstance(mock_side_effect_or_return_value, list):
        mock_generate_content.side_effect = mock_side_effect_or_return_value
    else:
        mock_generate_content.return_value = mock_side_effect_or_return_value

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected) as exc_info:
            gemini_client._fetch_from_api(
                prompt=mock_context["prompt"],
                schema=mock_context["schema"],
                error_tip=mock_context["error_tip"],
                cache_key=mock_context["cache_key"],
            )
        assert (
            getattr(exc_info.value, "tip", None)
            == "The Gemini API is currently overloaded. Please wait a few minutes and try again."
        )
        assert mock_generate_content.call_count == expected_call_count
    else:
        result = gemini_client._fetch_from_api(
            prompt=mock_context["prompt"],
            schema=mock_context["schema"],
            error_tip=mock_context["error_tip"],
            cache_key=mock_context["cache_key"],
        )
        assert result == expected
        assert mock_generate_content.call_count == expected_call_count
