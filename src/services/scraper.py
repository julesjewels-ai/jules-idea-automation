"""Web scraping utilities with content validation."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from src.utils.security import ScrapingError, validate_url

__all__ = ["scrape_text", "ScrapingError", "MIN_CONTENT_LENGTH", "BLOCKED_INDICATORS"]

# Minimum characters required to consider the page has meaningful content
MIN_CONTENT_LENGTH = 200

# Common phrases that indicate the page couldn't be accessed properly
BLOCKED_INDICATORS = [
    "sign in",
    "log in",
    "login",
    "access denied",
    "page not found",
    "404",
    "forbidden",
    "javascript required",
    "enable javascript",
    "cookies required",
]


def scrape_text(url: str) -> str:
    """Fetch the content of a URL and extracts validated text.

    Args:
    ----
        url: The URL to scrape

    Returns:
    -------
        Extracted text content

    Raises:
    ------
        ScrapingError: If the page cannot be scraped or has
                      insufficient content

    """
    validate_url(url)

    response = _fetch_response(url)

    try:
        text = _extract_text(response.content)
        _validate_content(text, url)
        return text

    except Exception as e:
        if isinstance(e, ScrapingError):
            raise
        raise ScrapingError(f"Failed to scrape {url}: {e}", tip="An unexpected error occurred during scraping.")


def _extract_text(content: bytes) -> str:
    """Extract clean text from HTML content.

    Args:
    ----
        content: The HTML content in bytes

    Returns:
    -------
        Cleaned text

    """
    soup = BeautifulSoup(content, "html.parser")

    # Remove script, style, nav, header, footer elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
        element.decompose()

    # Get text
    text = soup.get_text()

    # Break into lines and remove leading/trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)

    return text


def _fetch_response(url: str) -> requests.Response:
    """Fetch the URL and handles network errors.

    Args:
    ----
        url: The URL to fetch

    Returns:
    -------
        The response object

    Raises:
    ------
        ScrapingError: If the network request fails

    """
    try:
        headers = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")}
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        return response

    except requests.exceptions.HTTPError as e:
        tip = "Check if the URL is correct and accessible in your browser."
        if e.response.status_code == 403:
            tip = "The website is blocking automated access (403 Forbidden). Try a different source."
        elif e.response.status_code == 404:
            tip = "The page was not found (404). Check the URL for typos."
        raise ScrapingError(f"HTTP error accessing {url}: {e}", tip=tip)
    except requests.exceptions.Timeout:
        raise ScrapingError(
            f"Timeout accessing {url}",
            tip=("The website is taking too long to respond. It might be down or blocking connections."),
        )
    except requests.exceptions.RequestException as e:
        raise ScrapingError(
            f"Network error accessing {url}: {e}", tip="Check your internet connection and DNS settings."
        )
    except Exception as e:
        raise ScrapingError(f"Failed to scrape {url}: {e}", tip="An unexpected error occurred during scraping.")


def _validate_content(text: str, url: str) -> None:
    """Validate that scraped content is sufficient and meaningful.

    Args:
    ----
        text: The scraped text content
        url: The original URL (for error messages)

    Raises:
    ------
        ScrapingError: If content is insufficient or appears blocked

    """
    # Check minimum length
    if len(text) < MIN_CONTENT_LENGTH:
        raise ScrapingError(
            f"Insufficient content from {url}. "
            f"Only {len(text)} characters extracted "
            f"(minimum: {MIN_CONTENT_LENGTH}). "
            "The page may require authentication or JavaScript.",
            tip=("The page content is too short. Try a different URL or ensure the page doesn't require login/JS."),
        )

    # Check for blocked/login indicators in first portion of text
    text_lower = text[:1000].lower()
    for indicator in BLOCKED_INDICATORS:
        # Only flag if the indicator appears prominently (not just in passing)
        if text_lower.count(indicator) >= 2:
            raise ScrapingError(
                f"Page at {url} appears to require authentication or is blocked. Detected '{indicator}' indicators.",
                tip=("The website seems to require login or has blocked the scraper. Try a public, static page."),
            )
