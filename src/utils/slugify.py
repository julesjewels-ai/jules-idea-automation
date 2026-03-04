"""Slugification utility for converting text to GitHub-compatible repository names."""

from __future__ import annotations

import re


def slugify(text: str, max_length: int = 100) -> str:
    """Convert text to a kebab-case slug suitable for GitHub repository names.

    Args:
    ----
        text: The text to slugify
        max_length: Maximum slug length (GitHub limit is 100 characters)

    Returns:
    -------
        A kebab-case slug, truncated to max_length if necessary

    Examples:
    --------
        >>> slugify("My Cool Project")
        'my-cool-project'
        >>> slugify("Hello, World!")
        'hello-world'
        >>> slugify("Test@#$%Tool")
        'test-tool'

    """
    # Convert to lowercase
    text = text.lower()

    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Strip leading and trailing hyphens
    text = text.strip("-")

    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length]
        # Strip any trailing hyphens after truncation
        text = text.rstrip("-")

    return text
