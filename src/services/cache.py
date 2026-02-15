"""Cache service implementation."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

from src.core.interfaces import CacheProvider
from src.utils.errors import CacheError


logger = logging.getLogger(__name__)


class FileCacheProvider(CacheProvider):
    """File-based cache implementation.

    Stores cached items as JSON files in a specified directory.
    Uses SHA-256 hashing for keys to ensure filesystem safety.
    """

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """Initialize the file cache provider.

        Args:
            cache_dir: Directory to store cache files.
                Defaults to .jules/cache.
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.cwd() / ".jules" / "cache"

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise CacheError(
                f"Failed to create cache directory: {e}"
            )

    def _get_cache_path(self, key: str) -> Path:
        """Generate a safe file path for a cache key."""
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The unique cache key.

        Returns:
            The cached value or None if not found.
        """
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the cache.

        Args:
            key: The unique cache key.
            value: The value to store.
            ttl: Optional time-to-live.
        """
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(value, f)
        except (TypeError, OSError) as e:
            logger.warning(f"Failed to write cache for key '{key}': {e}")
