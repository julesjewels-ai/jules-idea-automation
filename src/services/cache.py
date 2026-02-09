"""Persistent caching service implementation."""

import hashlib
import json
import logging
import os
from typing import Any, Optional

from src.core.interfaces import CacheProvider
from src.utils.errors import CacheError


logger = logging.getLogger(__name__)


class FileCacheProvider:
    """A file-based cache provider that stores data in JSON files."""

    def __init__(self, cache_dir: str = ".jules/cache") -> None:
        """Initialize the file cache provider.

        Args:
            cache_dir: The directory to store cache files.
        """
        self.cache_dir = cache_dir
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            raise CacheError(f"Failed to create cache directory {self.cache_dir}: {e}", tip="Check directory permissions.")

    def _get_path(self, key: str) -> str:
        """Generate a safe file path for a cache key.

        Args:
            key: The raw cache key.

        Returns:
            The absolute path to the cache file.
        """
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The unique cache key.

        Returns:
            The cached value (deserialized JSON) if found, None otherwise.
        """
        path = self._get_path(key)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Cache read error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache.

        Args:
            key: The unique cache key.
            value: The value to store (must be JSON serializable).
        """
        path = self._get_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")
