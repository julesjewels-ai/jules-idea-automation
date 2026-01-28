"""Security utilities."""

import socket
import ipaddress
from urllib.parse import urlparse
from src.utils.errors import AppError

class ScrapingError(AppError):
    """Raised when scraping fails or returns insufficient content."""
    pass

def validate_url(url: str) -> None:
    """Validate that the URL is safe to scrape.

    Prevents SSRF by blocking access to local/private network addresses.

    Args:
        url: The URL to validate

    Raises:
        ScrapingError: If the URL is invalid or unsafe
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            raise ScrapingError(
                f"Invalid scheme: {parsed.scheme}. Only http/https allowed.",
                tip="Please provide a URL starting with http:// or https://."
            )

        hostname = parsed.hostname
        if not hostname:
            raise ScrapingError(
                "Invalid URL: No hostname found",
                tip="Check the URL format. It should look like https://example.com"
            )

        # Resolve hostname to IP
        try:
            ip_str = socket.gethostbyname(hostname)
        except socket.gaierror:
            raise ScrapingError(
                f"Could not resolve hostname: {hostname}",
                tip="The domain name could not be resolved. Check for typos or your internet connection."
            )

        ip = ipaddress.ip_address(ip_str)

        # Check for private/local IPs
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved:
             raise ScrapingError(
                 f"Access to private/local address {hostname} ({ip_str}) is blocked for security.",
                 tip="For security reasons, this tool can only scrape public websites, not local or private network addresses."
             )

    except ValueError:
        raise ScrapingError(
            f"Invalid URL format: {url}",
            tip="The URL provided is not valid. Please check for typos."
        )
