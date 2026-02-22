"""Caching service implementation."""

from __future__ import annotations

import os
import json
import logging
import hashlib
import time
from typing import Any, Optional
from pathlib import Path

from src.core.interfaces import CacheProvider


logger = logging.getLogger(__name__)


class FileCacheProvider(CacheProvider):
    """File-based caching implementation.

    Stores cached items as JSON files in a local directory.
    Uses SHA256 hashing for cache keys to ensure safe filenames.
    """

    def __init__(self, cache_dir: str = ".cache/gemini") -> None:
        """Initialize the cache provider.

        Args:
            cache_dir: The directory to store cache files.
        """
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(
                f"Failed to create cache directory {cache_dir}: {e}")
            # If we can't create the directory, subsequent ops will fail
            # gracefully

    def _get_cache_path(self, key: str) -> Path:
        """Generate a safe file path for the given key."""
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

            # Check TTL
            expires_at = data.get("expires_at")
            if expires_at and time.time() > expires_at:
                logger.debug(f"Cache expired for key: {key}")
                self.delete(key)
                return None

            logger.debug(f"Cache hit for key: {key}")
            return data.get("value")

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value in the cache."""
        cache_path = self._get_cache_path(key)

        data = {
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl if ttl else None
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cache set for key: {key}")
        except OSError as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")

    def delete(self, key: str) -> None:
        """Remove a value from the cache."""
        cache_path = self._get_cache_path(key)
        try:
            if cache_path.exists():
                os.remove(cache_path)
                logger.debug(f"Cache deleted for key: {key}")
        except OSError as e:
            logger.warning(f"Failed to delete cache for key {key}: {e}")
