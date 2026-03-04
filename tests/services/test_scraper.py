import pytest

from src.services.scraper import ScrapingError, scrape_text


def test_validate_url_local_blocked() -> None:
    with pytest.raises(ScrapingError, match="Access to private/local address"):
        scrape_text("http://localhost:8080")


def test_validate_url_loopback_blocked() -> None:
    with pytest.raises(ScrapingError, match="Access to private/local address"):
        scrape_text("http://127.0.0.1")


def test_validate_url_private_blocked() -> None:
    with pytest.raises(ScrapingError, match="Access to private/local address"):
        scrape_text("http://192.168.1.1")


def test_validate_url_invalid_scheme() -> None:
    with pytest.raises(ScrapingError, match="Invalid scheme"):
        scrape_text("ftp://example.com")


def test_validate_url_no_hostname() -> None:
    with pytest.raises(ScrapingError, match="Invalid URL"):
        scrape_text("http://")


def test_scraping_error_has_tip() -> None:
    """Test that ScrapingError includes a tip."""
    with pytest.raises(ScrapingError) as excinfo:
        # Trigger an error known to have a tip (e.g. invalid scheme)
        scrape_text("ftp://example.com")

    assert excinfo.value.tip is not None
    assert "Please provide a URL starting with http:// or https://" in excinfo.value.tip
