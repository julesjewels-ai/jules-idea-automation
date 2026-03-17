from typing import Any, Type, Union
from unittest.mock import MagicMock

import pytest
from google.genai import errors
from pytest_mock import MockerFixture

from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError


class MockAPIError(errors.APIError):  # type: ignore[misc]
    def __init__(self, message: str) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": {"message": message}}
        super().__init__(code=503, response=mock_resp)


@pytest.fixture
def gemini_client(mocker: MockerFixture) -> GeminiClient:
    mocker.patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"})
    client = GeminiClient(api_key="test_key")
    return client


@pytest.fixture
def mock_schema() -> dict[str, Any]:
    return {"type": "object", "properties": {"idea": {"type": "string"}}}


@pytest.mark.parametrize(
    "models_config, mock_responses, expected_result",
    [
        (
            # Happy Path
            ["gemini-3-pro-preview", "gemini-2.5-flash"],
            [{"text": '{"idea": "great idea"}'}],
            {"idea": "great idea"},
        ),
        (
            # Edge Case: Fallback on 503
            ["gemini-3-pro-preview", "gemini-2.5-flash"],
            [MockAPIError("503 UNAVAILABLE"), {"text": '{"idea": "fallback idea"}'}],
            {"idea": "fallback idea"},
        ),
        (
            # Error State: All models fail
            ["gemini-3-pro-preview", "gemini-2.5-flash"],
            [MockAPIError("500 INTERNAL ERROR"), MockAPIError("500 INTERNAL ERROR")],
            GenerationError,
        ),
    ],
)
def test_fetch_from_api_behavior(
    gemini_client: GeminiClient,
    mocker: MockerFixture,
    mock_schema: dict[str, Any],
    models_config: list[str],
    mock_responses: list[Union[dict[str, str], Exception]],
    expected_result: Union[dict[str, Any], Type[Exception]],
) -> None:
    # Namespace Verified: patching internal client to prevent drift
    mock_generate = mocker.patch.object(gemini_client.client.models, "generate_content", autospec=True)

    # Configure mock responses sequentially
    side_effects = []
    for resp in mock_responses:
        if isinstance(resp, Exception):
            side_effects.append(resp)
        else:
            mock_obj = MagicMock()
            mock_obj.text = resp["text"]
            side_effects.append(mock_obj)

    mock_generate.side_effect = side_effects

    # Mock _process_api_response to avoid needing precise API JSON formatting
    mock_process = mocker.patch.object(gemini_client, "_process_api_response", autospec=True)

    # Setup _process_api_response to return what we expect if successful
    if not isinstance(expected_result, type):
        mock_process.return_value = expected_result

    gemini_client.models = models_config

    prompt = "test prompt"
    error_tip = "test tip"
    cache_key = "test_key"

    if isinstance(expected_result, type) and issubclass(expected_result, Exception):
        with pytest.raises(expected_result):
            gemini_client._fetch_from_api(prompt, mock_schema, error_tip, cache_key)
    else:
        result = gemini_client._fetch_from_api(prompt, mock_schema, error_tip, cache_key)
        assert result == expected_result

        # Verify side effects
        mock_process.assert_called_once_with(
            mock_responses[-1]["text"] if isinstance(mock_responses[-1], dict) else mock_responses[-1],
            mock_schema,
            cache_key,
            error_tip,
        )

    # Verify generate_content side effect
    assert mock_generate.call_count == len(mock_responses)
