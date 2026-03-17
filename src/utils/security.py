"""Security utilities."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import ParseResult, urlparse

from src.utils.errors import ScrapingError


def validate_url(url: str) -> None:
    """Validate that the URL is safe to scrape.

    Prevents SSRF by blocking access to local/private network addresses.

    Args:
    ----
        url: The URL to validate

    Raises:
    ------
        ScrapingError: If the URL is invalid or unsafe

    """
    try:
        parsed = _parse_and_validate_scheme(url)
        hostname = _validate_hostname(parsed)
        ip = _resolve_ip(hostname)
        _validate_ip_safety(ip, hostname)

    except ValueError:
        raise ScrapingError(f"Invalid URL format: {url}", tip="The URL provided is not valid. Please check for typos.")


def _parse_and_validate_scheme(url: str) -> ParseResult:
    """Parse URL and validate scheme."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ScrapingError(
            f"Invalid scheme: {parsed.scheme}. Only http/https allowed.",
            tip="Please provide a URL starting with http:// or https://.",
        )
    return parsed


def _validate_hostname(parsed: ParseResult) -> str:
    """Validate and extract hostname."""
    hostname = parsed.hostname
    if not hostname:
        raise ScrapingError(
            "Invalid URL: No hostname found", tip="Check the URL format. It should look like https://example.com"
        )
    return hostname


def _resolve_ip(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Resolve hostname to IP address."""
    try:
        ip_str = socket.gethostbyname(hostname)
        return ipaddress.ip_address(ip_str)
    except socket.gaierror:
        raise ScrapingError(
            f"Could not resolve hostname: {hostname}",
            tip="The domain name could not be resolved. Check for typos or your internet connection.",
        )


def _validate_ip_safety(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, hostname: str) -> None:
    """Check if IP is safe (public)."""
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved:
        raise ScrapingError(
            f"Access to private/local address {hostname} ({ip}) is blocked for security.",
            tip="For security reasons, this tool can only scrape public "
            "websites, not local or private network addresses.",
        )
