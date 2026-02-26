import pytest
import requests
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from src.services.scraper import _fetch_response, ScrapingError

@pytest.fixture
def mock_response() -> MagicMock:
    """Fixture for a mock requests.Response object."""
    resp = MagicMock(spec=requests.Response)
    resp.content = b"<html>Content</html>"
    resp.status_code = 200
    return resp

@pytest.mark.parametrize("status_code, exception_type, expected_tip, exception_cls", [
    (200, None, None, None),  # Happy Path
    (403, requests.exceptions.HTTPError, "blocking automated access", ScrapingError), # Edge Case: Forbidden
    (404, requests.exceptions.HTTPError, "page was not found", ScrapingError),        # Edge Case: Not Found
    (500, requests.exceptions.HTTPError, "Check if the URL is correct", ScrapingError), # Generic HTTP Error
    (None, requests.exceptions.Timeout, "taking too long", ScrapingError),            # Error State: Timeout
    (None, requests.exceptions.ConnectionError, "Check your internet connection", ScrapingError), # Error State: Connection Error
    (None, Exception, "unexpected error", ScrapingError),                              # Error State: Generic Exception
])
def test_fetch_response_behavior(
    mocker: MockerFixture,
    mock_response: MagicMock,
    status_code: int | None,
    exception_type: type[Exception] | None,
    expected_tip: str | None,
    exception_cls: type[Exception] | None
) -> None:
    # 1. Setup Mocks (Namespace Verified: patching src.services.scraper.requests.get)
    mock_get = mocker.patch("src.services.scraper.requests.get")

    url = "http://example.com"

    if status_code == 200:
        # Happy Path: No exception, return response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # 2. Execution & Validation
        result = _fetch_response(url)
        assert result == mock_response
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    elif exception_type and issubclass(exception_type, requests.exceptions.HTTPError):
        # HTTP Errors are raised by raise_for_status()
        mock_response.status_code = status_code
        http_error = exception_type(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        # 2. Execution & Validation
        with pytest.raises(exception_cls) as excinfo:
            _fetch_response(url)

        assert expected_tip in excinfo.value.tip
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    elif exception_type:
        # Network errors (Timeout, ConnectionError, etc.) happen during requests.get()
        mock_get.side_effect = exception_type("Network Error")

        # 2. Execution & Validation
        with pytest.raises(exception_cls) as excinfo:
            _fetch_response(url)

        assert expected_tip in excinfo.value.tip
        mock_get.assert_called_once()
