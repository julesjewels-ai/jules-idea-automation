import pytest

from src.services.scraper import ScrapingError, scrape_text


def test_validate_url_local_blocked():
    with pytest.raises(ScrapingError, match="Access to private/local address"):
        scrape_text("http://localhost:8080")


def test_validate_url_loopback_blocked():
    with pytest.raises(ScrapingError, match="Access to private/local address"):
        scrape_text("http://127.0.0.1")


def test_validate_url_private_blocked():
    with pytest.raises(ScrapingError, match="Access to private/local address"):
        scrape_text("http://192.168.1.1")


def test_validate_url_invalid_scheme():
    with pytest.raises(ScrapingError, match="Invalid scheme"):
        scrape_text("ftp://example.com")


def test_validate_url_no_hostname():
    with pytest.raises(ScrapingError, match="Invalid URL"):
        scrape_text("http://")


# We can't easily test valid external URLs without internet access or mocking requests.
# But we can verify that validation passes for a valid-looking public IP if we mock socket.gethostbyname
# or if we trust the logic.
# For now, let's stick to negative tests which are most important for security.
