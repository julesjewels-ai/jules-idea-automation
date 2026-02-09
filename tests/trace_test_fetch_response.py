import pytest
from pytest_mock import MockerFixture
import requests
from typing import Any, Union, cast
from src.services.scraper import _fetch_response
from src.utils.security import ScrapingError

@pytest.fixture
def mock_context() -> dict[str, Any]:
    """Fixture for shared context."""
    return {
        "timeout": 15,
        "headers": {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    }

@pytest.mark.parametrize("url, mock_behavior, expected_result_or_error, expected_tip_fragment", [
    # Happy Path
    ("http://example.com", {"status_code": 200, "content": b"Success"}, "Success", None),

    # Edge Case: Timeout
    ("http://timeout.com", requests.exceptions.Timeout("Timeout"), ScrapingError, "taking too long"),

    # Error State: 403 Forbidden
    ("http://forbidden.com", (403, "Forbidden"), ScrapingError, "blocking automated access"),

    # Error State: 404 Not Found
    ("http://notfound.com", (404, "Not Found"), ScrapingError, "page was not found"),

    # Error State: Generic Request Exception
    ("http://error.com", requests.exceptions.RequestException("Generic Error"), ScrapingError, "Check your internet connection"),
])
def test_fetch_response_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, Any],
    url: str,
    mock_behavior: Union[dict[str, Any], Exception, tuple[int, str]],
    expected_result_or_error: Union[str, type[Exception]],
    expected_tip_fragment: str | None
) -> None:
    # 1. Setup Mocks (Namespace Verified: src.services.scraper imports requests)
    # Patch the requests module where it is used
    mock_requests = mocker.patch("src.services.scraper.requests")
    # Restore real exceptions so they can be caught in try/except blocks
    mock_requests.exceptions = requests.exceptions

    # Create a mock response object
    mock_resp = mocker.Mock(spec=requests.Response)

    # Configure mock based on behavior
    if isinstance(mock_behavior, dict):
        # Happy Path
        mock_resp.status_code = mock_behavior["status_code"]
        mock_resp.content = mock_behavior["content"]
        # raise_for_status does nothing on success
        mock_resp.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_resp

    elif isinstance(mock_behavior, tuple):
        # HTTP Error (Status Code, Message)
        status_code, msg = mock_behavior
        mock_resp.status_code = status_code

        # create the HTTPError and attach the response
        http_error = requests.exceptions.HTTPError(msg)
        http_error.response = mock_resp

        # When raise_for_status is called, it raises this error
        mock_resp.raise_for_status.side_effect = http_error
        mock_requests.get.return_value = mock_resp

    elif isinstance(mock_behavior, Exception):
        # Network/Timeout Error - occurs during .get()
        mock_requests.get.side_effect = mock_behavior

    # 2. Execution & Validation
    if isinstance(expected_result_or_error, type) and issubclass(expected_result_or_error, Exception):
        with pytest.raises(expected_result_or_error) as excinfo:
            _fetch_response(url)

        # Verify the tip if provided
        if expected_tip_fragment:
            scraping_error = cast(ScrapingError, excinfo.value)
            assert scraping_error.tip is not None
            assert expected_tip_fragment in scraping_error.tip

    else:
        # Happy Path Validation
        result = _fetch_response(url)
        assert result == mock_resp
        assert result.content == expected_result_or_error.encode()
        mock_resp.raise_for_status.assert_called_once()

    # 3. Verify Mock Interaction (Side Effects)
    mock_requests.get.assert_called_once()
    call_args = mock_requests.get.call_args
    assert call_args[0][0] == url
    assert call_args[1]["timeout"] == mock_context["timeout"]
    assert "User-Agent" in call_args[1]["headers"]
