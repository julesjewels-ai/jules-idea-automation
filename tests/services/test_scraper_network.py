
import pytest
import requests
from src.services.scraper import scrape_text, ScrapingError

def test_scrape_text_success(requests_mock):
    url = "http://example.com"
    content = "<html><body><p>Some meaningful content here that is long enough.</p>" * 10 + "</body></html>"
    requests_mock.get(url, text=content)

    result = scrape_text(url)
    assert "Some meaningful content" in result

def test_scrape_text_403_forbidden(requests_mock):
    url = "http://example.com/forbidden"
    requests_mock.get(url, status_code=403)

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert "blocking automated access" in excinfo.value.tip
    assert "403" in str(excinfo.value)

def test_scrape_text_404_not_found(requests_mock):
    url = "http://example.com/notfound"
    requests_mock.get(url, status_code=404)

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert "page was not found" in excinfo.value.tip
    assert "404" in str(excinfo.value)

def test_scrape_text_timeout(requests_mock):
    url = "http://example.com/timeout"
    requests_mock.get(url, exc=requests.exceptions.Timeout)

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert "taking too long" in excinfo.value.tip
    assert "Timeout accessing" in str(excinfo.value)

def test_scrape_text_connection_error(requests_mock):
    url = "http://example.com/error"
    requests_mock.get(url, exc=requests.exceptions.ConnectionError)

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert "Check your internet connection" in excinfo.value.tip
    assert "Network error" in str(excinfo.value)

def test_scrape_text_generic_exception(requests_mock):
    url = "http://example.com/oops"
    requests_mock.get(url, exc=Exception("Something weird"))

    with pytest.raises(ScrapingError) as excinfo:
        scrape_text(url)

    assert "unexpected error" in excinfo.value.tip
    assert "Failed to scrape" in str(excinfo.value)
