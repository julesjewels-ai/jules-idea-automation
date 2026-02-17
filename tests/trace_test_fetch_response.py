import pytest
import requests
from pytest_mock import MockerFixture
from src.services.scraper import _fetch_response, ScrapingError

@pytest.fixture
def mock_response_obj(mocker: MockerFixture) -> requests.Response:
    """Fixture to create a mock Response object with standard attributes."""
    resp = mocker.Mock(spec=requests.Response)
    resp.content = b"<html>Content</html>"
    resp.status_code = 200
    # raise_for_status is a method, so we mock it.
    # By default, it does nothing (success).
    resp.raise_for_status = mocker.Mock()
    return resp

@pytest.mark.parametrize("scenario, status_code, side_effect, expected_result, expected_tip_snippet", [
    # Happy Path
    ("success_200", 200, None, "return_response", None),

    # Edge Case: 403 Forbidden
    ("error_403", 403, requests.exceptions.HTTPError("403 Forbidden"), ScrapingError, "blocking automated access"),

    # Edge Case: 404 Not Found
    ("error_404", 404, requests.exceptions.HTTPError("404 Not Found"), ScrapingError, "page was not found"),

    # Error State: Timeout
    ("error_timeout", None, requests.exceptions.Timeout("Timed out"), ScrapingError, "taking too long"),

    # Error State: Connection Error (RequestException)
    ("error_connection", None, requests.exceptions.ConnectionError("Connection refused"), ScrapingError, "Check your internet connection"),

    # Error State: Generic Exception
    ("error_generic", None, Exception("Boom"), ScrapingError, "unexpected error"),
])
def test_fetch_response_behavior(
    mocker: MockerFixture,
    mock_response_obj: requests.Response,
    scenario: str,
    status_code: int | None,
    side_effect: Exception | None,
    expected_result: str | type[Exception],
    expected_tip_snippet: str | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # We patch requests.get in src.services.scraper to intercept the call.
    mock_get = mocker.patch("src.services.scraper.requests.get", autospec=True)

    url = "http://example.com"

    # Configure the mock behavior
    if scenario.startswith("success"):
        mock_get.return_value = mock_response_obj
    elif scenario.startswith("error_403") or scenario.startswith("error_404"):
        # For HTTP errors, requests.get returns a response, but raise_for_status raises exception
        mock_response_obj.status_code = status_code
        # Attach the response to the exception if it's an HTTPError
        if isinstance(side_effect, requests.exceptions.HTTPError):
            side_effect.response = mock_response_obj

        mock_response_obj.raise_for_status.side_effect = side_effect
        mock_get.return_value = mock_response_obj
    else:
        # For network errors (Timeout, ConnectionError), get() raises directly
        mock_get.side_effect = side_effect

    # 2. Execution & Validation
    if isinstance(expected_result, type) and issubclass(expected_result, Exception):
        with pytest.raises(expected_result) as exc_info:
            _fetch_response(url)

        # Verify the tip if expected
        if expected_tip_snippet:
            assert expected_tip_snippet in exc_info.value.tip

    else:
        # Happy path
        result = _fetch_response(url)
        assert result == mock_response_obj

        # Verify call arguments
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == url
        assert kwargs["timeout"] == 15
        assert "User-Agent" in kwargs["headers"]
        assert "Mozilla/5.0" in kwargs["headers"]["User-Agent"]
