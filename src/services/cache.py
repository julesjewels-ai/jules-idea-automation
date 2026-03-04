"""File-based implementation of the CacheProvider protocol."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from src.core.interfaces import CacheProvider

logger = logging.getLogger(__name__)


class FileCacheProvider(CacheProvider):
    """File-based cache implementation using JSON files."""

    def __init__(self, cache_dir: str = ".cache/gemini") -> None:
        """Initialize the file cache provider.

        Args:
        ----
            cache_dir: Directory to store cache files.

        """
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create cache directory {cache_dir}: {e}")

    def _get_path(self, key: str) -> Path:
        """Generate a file path from a cache key."""
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve a value from the cache.

        Args:
        ----
            key: The unique cache key.

        Returns:
        -------
            The cached value as a dictionary, or None if not found or on error.

        """
        path = self._get_path(key)
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            return json.loads(content)  # type: ignore[no-any-return]
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read cache for key {key}: {e}")
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a value in the cache.

        Args:
        ----
            key: The unique cache key.
            value: The value to cache (must be JSON-serializable).

        """
        path = self._get_path(key)
        try:
            content = json.dumps(value, indent=2)
            path.write_text(content, encoding="utf-8")
        except (OSError, TypeError) as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")
