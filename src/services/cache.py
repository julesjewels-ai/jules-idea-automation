"""File-based cache provider."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from src.core.interfaces import CacheProvider

logger = logging.getLogger(__name__)


class FileCacheProvider(CacheProvider):
    """File-based implementation of CacheProvider."""

    def __init__(self, cache_dir: str = ".cache/gemini") -> None:
        """Initialize the file cache provider.

        Args:
            cache_dir: Directory to store cache files.
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create cache directory {self.cache_dir}: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a given cache key."""
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        self._ensure_cache_dir()
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
        except (TypeError, OSError) as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")

    def delete(self, key: str) -> None:
        """Remove a value from the cache."""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                os.remove(cache_path)
            except OSError as e:
                logger.warning(f"Failed to delete cache for key {key}: {e}")
