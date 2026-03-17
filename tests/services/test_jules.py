"""Tests for JulesClient."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.jules import JulesClient
from src.utils.errors import JulesApiError
from tests.conftest import make_http_error


def test_jules_client_api_error_401() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.http_client.requests.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = make_http_error(401)
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "Your Jules API key seems invalid" in excinfo.value.tip


def test_jules_client_api_error_403() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.http_client.requests.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = make_http_error(403)
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "You don't have permission" in excinfo.value.tip


def test_jules_client_api_error_404() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.http_client.requests.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = make_http_error(404)
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "The requested resource was not found" in excinfo.value.tip


def test_jules_client_generic_error() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.http_client.requests.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = make_http_error(500)
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "API returned status 500" in excinfo.value.tip


def test_jules_client_json_error() -> None:
    client = JulesClient(api_key="test-key")

    with patch("src.services.http_client.requests.request") as mock_request:
        error_json = {"error": {"message": "Custom API Error"}}
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = make_http_error(400, error_json)
        mock_request.return_value = mock_resp

        with pytest.raises(JulesApiError) as excinfo:
            client.list_sources()

        assert excinfo.value.tip is not None and "API Message: Custom API Error" in excinfo.value.tip
