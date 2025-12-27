"""Web scraping utilities with content validation."""

import requests
from bs4 import BeautifulSoup


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


class ScrapingError(Exception):
    """Raised when scraping fails or returns insufficient content."""
    pass


def scrape_text(url: str) -> str:
    """Fetches the content of a URL and extracts validated text.
    
    Args:
        url: The URL to scrape
        
    Returns:
        Extracted text content
        
    Raises:
        ScrapingError: If the page cannot be scraped or has insufficient content
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
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
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Validate content
        _validate_content(text, url)
        
        return text
        
    except ScrapingError:
        raise
    except requests.exceptions.HTTPError as e:
        raise ScrapingError(f"HTTP error accessing {url}: {e}")
    except requests.exceptions.Timeout:
        raise ScrapingError(f"Timeout accessing {url}")
    except requests.exceptions.RequestException as e:
        raise ScrapingError(f"Network error accessing {url}: {e}")
    except Exception as e:
        raise ScrapingError(f"Failed to scrape {url}: {e}")


def _validate_content(text: str, url: str) -> None:
    """Validate that scraped content is sufficient and meaningful.
    
    Args:
        text: The scraped text content
        url: The original URL (for error messages)
        
    Raises:
        ScrapingError: If content is insufficient or appears blocked
    """
    # Check minimum length
    if len(text) < MIN_CONTENT_LENGTH:
        raise ScrapingError(
            f"Insufficient content from {url}. "
            f"Only {len(text)} characters extracted (minimum: {MIN_CONTENT_LENGTH}). "
            "The page may require authentication or JavaScript."
        )
    
    # Check for blocked/login indicators in first portion of text
    text_lower = text[:1000].lower()
    for indicator in BLOCKED_INDICATORS:
        # Only flag if the indicator appears prominently (not just in passing)
        if text_lower.count(indicator) >= 2:
            raise ScrapingError(
                f"Page at {url} appears to require authentication or is blocked. "
                f"Detected '{indicator}' indicators."
            )
