import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock
import requests
from typing import Any
from src.services.scraper import _fetch_response, ScrapingError


@pytest.fixture
def mock_response(mocker: MockerFixture) -> MagicMock:
    return mocker.create_autospec(requests.Response, instance=True)


@pytest.mark.parametrize("url, mock_setup, expected_outcome", [
    # Happy Path
    (
        "http://valid.com",
        {"status_code": 200, "content": b"valid content"},
        "success"
    ),
    # Edge Case: 403 Forbidden
    (
        "http://forbidden.com",
        {"status_code": 403, "http_error": True},
        (
            "HTTP error accessing",
            "The website is blocking automated access (403 Forbidden). "
            "Try a different source."
        )
    ),
    # Edge Case: 404 Not Found
    (
        "http://missing.com",
        {"status_code": 404, "http_error": True},
        (
            "HTTP error accessing",
            "The page was not found (404). Check the URL for typos."
        )
    ),
    # Error State: Timeout
    (
        "http://timeout.com",
        {"side_effect": requests.exceptions.Timeout("Read timed out")},
        (
            "Timeout accessing",
            "The website is taking too long to respond. "
            "It might be down or blocking connections."
        )
    ),
    # Error State: Generic RequestException
    (
        "http://error.com",
        {"side_effect": requests.exceptions.RequestException("Conn aborted")},
        (
            "Network error accessing",
            "Check your internet connection and DNS settings."
        )
    ),
    # Error State: Unexpected Exception
    (
        "http://unexpected.com",
        {"side_effect": ValueError("Something went wrong")},
        ("Failed to scrape", "An unexpected error occurred during scraping.")
    ),
])
def test_fetch_response_behavior(
    mocker: MockerFixture,
    mock_response: MagicMock,
    url: str,
    mock_setup: dict[str, Any],
    expected_outcome: str | tuple[str, str]
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # We patch 'src.services.scraper.requests.get' because the module imports
    # requests directly.
    mock_get = mocker.patch("src.services.scraper.requests.get")

    # Configure the mock response or side effect
    if "side_effect" in mock_setup:
        # Exceptions that happen during the get call itself (Timeout, etc.)
        mock_get.side_effect = mock_setup["side_effect"]
    elif mock_setup.get("http_error"):
        # HTTPError is raised by raise_for_status(), not get()
        resp = mock_response
        resp.status_code = mock_setup.get("status_code", 500)

        # Create the exception and attach the response to it
        error = requests.exceptions.HTTPError(f"{resp.status_code} Error")
        error.response = resp

        resp.raise_for_status.side_effect = error
        mock_get.return_value = resp
    else:
        # Happy path
        resp = mock_response
        resp.status_code = mock_setup.get("status_code", 200)
        resp.content = mock_setup.get("content", b"")
        resp.raise_for_status.return_value = None
        mock_get.return_value = resp

    # 2. Execution & Validation
    if isinstance(expected_outcome, tuple):
        expected_msg_part, expected_tip = expected_outcome
        with pytest.raises(ScrapingError) as excinfo:
            _fetch_response(url)

        assert expected_msg_part in str(excinfo.value)
        if expected_tip:
            assert excinfo.value.tip == expected_tip
    elif expected_outcome == "success":
        result = _fetch_response(url)
        assert result == mock_get.return_value

        # Verify call arguments
        expected_headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36'
            )
        }
        mock_get.assert_called_once_with(
            url, timeout=15, headers=expected_headers
        )
