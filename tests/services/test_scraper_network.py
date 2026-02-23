"""Tests for scraper network error handling."""

import pytest
from unittest.mock import patch, MagicMock
import requests
from src.services.scraper import scrape_text, ScrapingError


@patch("src.services.scraper._fetch_response")
def test_scrape_text_success(mock_fetch: MagicMock) -> None:
    url = "http://example.com"
    content = ("<html><body><p>Some meaningful content here that is long enough.</p>" * 10
               + "</body></html>")

    mock_response = MagicMock()
    mock_response.content = content.encode("utf-8")
    mock_fetch.return_value = mock_response

    result = scrape_text(url)
    assert "Some meaningful content" in result


@patch("src.services.scraper.requests.get")
def test_scrape_text_403_forbidden(mock_get: MagicMock) -> None:
    url = "http://example.com/forbidden"

    mock_response = MagicMock()
    mock_response.status_code = 403
    http_error = requests.exceptions.HTTPError(
        "403 Client Error: Forbidden", response=mock_response
    )
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = http_error
    mock_get.return_value = mock_resp

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert excinfo.value.tip is not None
    assert "blocking automated access" in excinfo.value.tip
    assert "403" in str(excinfo.value)


@patch("src.services.scraper.requests.get")
def test_scrape_text_404_not_found(mock_get: MagicMock) -> None:
    url = "http://example.com/notfound"

    mock_response = MagicMock()
    mock_response.status_code = 404
    http_error = requests.exceptions.HTTPError(
        "404 Client Error: Not Found", response=mock_response
    )
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = http_error
    mock_get.return_value = mock_resp

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert excinfo.value.tip is not None
    assert "page was not found" in excinfo.value.tip
    assert "404" in str(excinfo.value)


@patch("src.services.scraper.requests.get")
def test_scrape_text_timeout(mock_get: MagicMock) -> None:
    url = "http://example.com/timeout"
    mock_get.side_effect = requests.exceptions.Timeout()

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert excinfo.value.tip is not None
    assert "taking too long" in excinfo.value.tip
    assert "Timeout accessing" in str(excinfo.value)


@patch("src.services.scraper.requests.get")
def test_scrape_text_connection_error(mock_get: MagicMock) -> None:
    url = "http://example.com/error"
    mock_get.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert excinfo.value.tip is not None
    assert "Check your internet connection" in excinfo.value.tip
    assert "Network error" in str(excinfo.value)


@patch("src.services.scraper.requests.get")
def test_scrape_text_generic_exception(mock_get: MagicMock) -> None:
    url = "http://example.com/oops"
    mock_get.side_effect = Exception("Something weird")

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert excinfo.value.tip is not None
    assert "unexpected error" in excinfo.value.tip
    assert "Failed to scrape" in str(excinfo.value)
