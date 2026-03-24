"""Tests for BaseApiClient retry-with-backoff logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.services.http_client import BaseApiClient
from src.utils.errors import AppError
from tests.conftest import make_http_error, make_ok_response


def _make_client(**overrides: object) -> BaseApiClient:
    """Create a BaseApiClient with sensible test defaults."""
    defaults = {
        "base_url": "https://api.example.com",
        "headers": {"Authorization": "Bearer test"},
        "error_class": AppError,
        "service_name": "Test",
        "max_retries": 3,
        "retry_base_delay": 0.5,
    }
    defaults.update(overrides)
    return BaseApiClient(**defaults)  # type: ignore[arg-type]


# --- Retry on 5xx ---


@patch("src.services.http_client.time.sleep", return_value=None)
def test_retry_on_502_then_success(mock_sleep: MagicMock) -> None:
    """A 502 on the first attempt should be retried; success on second attempt returns data."""
    client = _make_client()

    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.exceptions = requests.exceptions
        mock_requests.request.side_effect = [
            make_http_error(502),  # attempt 1: transient error
            make_ok_response({"status": "ok"}),  # attempt 2: success
        ]

        # The first call raises HTTPError via side_effect, so we need
        # the mock to raise on the first call and return on the second.
        # make_http_error returns an exception, so side_effect will raise it.
        # make_ok_response returns a response object, so side_effect will return it.
        result = client._request("GET", "https://api.example.com/test")

        assert result == {"status": "ok"}
        assert mock_requests.request.call_count == 2
        mock_sleep.assert_called_once_with(0.5)


@patch("src.services.http_client.time.sleep", return_value=None)
def test_retry_on_503_exhausts_retries(mock_sleep: MagicMock) -> None:
    """Three consecutive 503 responses should exhaust retries and raise."""
    client = _make_client()

    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.exceptions = requests.exceptions
        mock_requests.request.side_effect = [
            make_http_error(503),
            make_http_error(503),
            make_http_error(503),
        ]

        with pytest.raises(AppError, match="after 3 attempts"):
            client._request("GET", "https://api.example.com/test")

        assert mock_requests.request.call_count == 3
        assert mock_sleep.call_count == 2  # sleep between attempt 1→2 and 2→3


# --- Retry on Timeout ---


@patch("src.services.http_client.time.sleep", return_value=None)
def test_retry_on_timeout_then_success(mock_sleep: MagicMock) -> None:
    """A Timeout on the first attempt should be retried; success on second attempt."""
    client = _make_client()

    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.exceptions = requests.exceptions
        mock_requests.request.side_effect = [
            requests.exceptions.Timeout(),  # attempt 1
            make_ok_response({"recovered": True}),  # attempt 2
        ]

        result = client._request("GET", "https://api.example.com/test")

        assert result == {"recovered": True}
        assert mock_requests.request.call_count == 2
        mock_sleep.assert_called_once_with(0.5)


# --- Retry on ConnectionError ---


@patch("src.services.http_client.time.sleep", return_value=None)
def test_retry_on_connection_error_then_success(mock_sleep: MagicMock) -> None:
    """A ConnectionError on the first attempt should be retried."""
    client = _make_client()

    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.exceptions = requests.exceptions
        mock_requests.request.side_effect = [
            requests.exceptions.ConnectionError("DNS resolution failed"),
            make_ok_response({"reconnected": True}),
        ]

        result = client._request("GET", "https://api.example.com/test")

        assert result == {"reconnected": True}
        assert mock_requests.request.call_count == 2
        mock_sleep.assert_called_once_with(0.5)


# --- No retry on 4xx ---


@patch("src.services.http_client.time.sleep", return_value=None)
def test_no_retry_on_4xx(mock_sleep: MagicMock) -> None:
    """4xx errors should raise immediately without retrying."""
    client = _make_client()

    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.exceptions = requests.exceptions
        mock_requests.request.side_effect = make_http_error(401)

        with pytest.raises(AppError, match="API Error"):
            client._request("GET", "https://api.example.com/test")

        assert mock_requests.request.call_count == 1
        mock_sleep.assert_not_called()


# --- Backoff delay verification ---


@patch("src.services.http_client.time.sleep", return_value=None)
def test_retry_backoff_delays(mock_sleep: MagicMock) -> None:
    """Backoff delays should increase exponentially: 0.5s, 1.0s."""
    client = _make_client()

    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.exceptions = requests.exceptions
        mock_requests.request.side_effect = [
            make_http_error(500),
            make_http_error(500),
            make_http_error(500),
        ]

        with pytest.raises(AppError):
            client._request("GET", "https://api.example.com/test")

        # Delays: 0.5 * 2^0 = 0.5, 0.5 * 2^1 = 1.0
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.5)
        mock_sleep.assert_any_call(1.0)
