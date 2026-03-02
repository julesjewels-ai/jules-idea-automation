import pytest
from pytest_mock import MockerFixture
import requests
from unittest.mock import MagicMock

from src.services.scraper import _fetch_response
from src.utils.security import ScrapingError

@pytest.fixture
def mock_context() -> dict[str, str]:
    return {"url": "https://example.com/test"}

@pytest.mark.parametrize("input_val, expected, status_code, exception_to_raise", [
    ("https://example.com/test", "valid_response", 200, None),  # Happy Path
    ("https://example.com/test", ScrapingError, 403, requests.exceptions.HTTPError()),  # Error State
    ("https://example.com/test", ScrapingError, 404, requests.exceptions.HTTPError()),  # Error State
    ("https://example.com/test", ScrapingError, None, requests.exceptions.Timeout()),  # Edge Case
    ("https://example.com/test", ScrapingError, None, requests.exceptions.RequestException()),  # Error State
    ("https://example.com/test", ScrapingError, None, ValueError("Unknown error")),  # Error State
])
def test__fetch_response_behavior(
    mocker: MockerFixture,
    mock_context: dict[str, str],
    input_val: str,
    expected: str | type[Exception],
    status_code: int | None,
    exception_to_raise: Exception | None
) -> None:
    # 1. Setup Mocks (Namespace Verified)
    # The module src.services.scraper uses `import requests`, so we patch `src.services.scraper.requests.get`
    # Memory: "When testing functions using import requests, patch the specific function (e.g., src.module.requests.get) rather than the entire module."
    mock_get = mocker.patch("src.services.scraper.requests.get", autospec=True)

    # Configure exception or return value
    if exception_to_raise:
        if isinstance(exception_to_raise, requests.exceptions.HTTPError):
            mock_response = MagicMock(spec=requests.Response)
            mock_response.status_code = status_code
            exception_to_raise.response = mock_response
        mock_get.side_effect = exception_to_raise
    else:
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = status_code
        mock_response.content = b"Success"
        mock_get.return_value = mock_response

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36'
        )
    }

    # 2. Execution & Validation
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            _fetch_response(input_val)
    else:
        result = _fetch_response(input_val)
        assert result == mock_response

    # Verify side effects
    mock_get.assert_called_once_with(input_val, timeout=15, headers=headers)
    if not exception_to_raise:
        mock_response.raise_for_status.assert_called_once()
