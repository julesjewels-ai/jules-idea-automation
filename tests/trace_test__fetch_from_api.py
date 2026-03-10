from typing import Any
from unittest.mock import MagicMock

import pytest
from google.genai import errors
from pytest_mock import MockerFixture
from requests.models import Response

from src.core.models import IdeaResponse
from src.services.gemini import GeminiClient
from src.utils.errors import GenerationError


@pytest.fixture
def target_client() -> GeminiClient:
    return GeminiClient(api_key="fake-test-key")


@pytest.fixture
def mock_context() -> dict[str, Any]:
    return {
        "prompt": "Test prompt",
        "schema": IdeaResponse,
        "error_tip": "Test error tip",
        "cache_key": "test_cache_key",
    }


class MockAPIError(errors.APIError):  # type: ignore[misc]
    def __init__(self, message: str, code: int) -> None:
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = code
        mock_resp.json.return_value = {"error": {"message": message, "code": code}}
        super().__init__(code=code, response=mock_resp)


@pytest.fixture
def successful_response() -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.text = '{"title": "Test App", "slug": "test-app", "description": "Test desc", "tech_stack": ["Python"], "features": ["Login"]}'
    return mock_resp


@pytest.mark.parametrize(
    "input_val, expected",
    [
        ("happy_path", "success"),
        ("edge_case_503_fallback", "success"),
        ("error_state_400", GenerationError),
    ],
)
def test_fetch_from_api_behavior(
    mocker: MockerFixture,
    target_client: GeminiClient,
    mock_context: dict[str, Any],
    input_val: str,
    expected: str | type[Exception],
    successful_response: MagicMock,
) -> None:
    # 1. Setup Mocks (Namespace Verified via patching target_client instance attribute)
    mock_generate = mocker.patch.object(target_client.client.models, "generate_content", autospec=True)

    if input_val == "happy_path":
        mock_generate.return_value = successful_response
    elif input_val == "edge_case_503_fallback":
        # First call fails with 503, second call succeeds
        error_503 = MockAPIError("503 UNAVAILABLE", 503)
        mock_generate.side_effect = [error_503, successful_response]
    elif input_val == "error_state_400":
        error_400 = MockAPIError("400 Bad Request", 400)
        mock_generate.side_effect = error_400

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            target_client._fetch_from_api(
                prompt=mock_context["prompt"],
                schema=mock_context["schema"],
                error_tip=mock_context["error_tip"],
                cache_key=mock_context["cache_key"],
            )
        mock_generate.assert_called_once()
    else:
        result = target_client._fetch_from_api(
            prompt=mock_context["prompt"],
            schema=mock_context["schema"],
            error_tip=mock_context["error_tip"],
            cache_key=mock_context["cache_key"],
        )
        assert result["title"] == "Test App"

        if input_val == "happy_path":
            mock_generate.assert_called_once()
        elif input_val == "edge_case_503_fallback":
            assert mock_generate.call_count == 2
