"""Tests for JulesClient."""

import pytest
from typing import Any
from unittest.mock import patch, MagicMock
import requests
from src.services.jules import JulesClient
from src.utils.errors import JulesApiError


def _make_http_error(status_code: int, text: str = "", json_data: Any = None) -> requests.exceptions.HTTPError:
    """Helper to create a requests.exceptions.HTTPError with a mock response."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    if json_data is not None:
        response.json.return_value = json_data
    else:
        response.json.side_effect = ValueError("No JSON")
    error = requests.exceptions.HTTPError(response=response)
    return error


def test_jules_client_api_error_401() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.jules.requests.request") as mock_request:
        mock_request.side_effect = _make_http_error(401, "Unauthorized")
        # The _request method catches HTTPError, so we need to simulate raise_for_status
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _make_http_error(401, "Unauthorized")
        mock_request.side_effect = None
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "Your Jules API key seems invalid" in excinfo.value.tip


def test_jules_client_api_error_403() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.jules.requests.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _make_http_error(403, "Forbidden")
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "You don't have permission" in excinfo.value.tip


def test_jules_client_api_error_404() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.jules.requests.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _make_http_error(404, "Not Found")
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "The requested resource was not found" in excinfo.value.tip


def test_jules_client_generic_error() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.jules.requests.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _make_http_error(500, "Internal Server Error")
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "API returned status 500" in excinfo.value.tip


def test_jules_client_json_error() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.jules.requests.request") as mock_request:
        error_json = {"error": {"message": "Custom API Error"}}
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _make_http_error(
            400, "Bad Request", json_data=error_json
        )
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "API Message: Custom API Error" in excinfo.value.tip
