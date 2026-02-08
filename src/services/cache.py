"""Cache service implementation."""

import json
import logging
import hashlib
import time
from typing import Any, Optional
from pathlib import Path

from src.core.interfaces import CacheProvider


logger = logging.getLogger(__name__)


class InMemoryCacheProvider(CacheProvider):
    """In-memory cache implementation for testing."""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        entry = self._cache.get(key)
        if not entry:
            return None

        expiry = entry.get("expiry")
        if expiry and time.time() > expiry:
            self.delete(key)
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        expiry = time.time() + ttl if ttl else None
        self._cache[key] = {"value": value, "expiry": expiry}

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()


class FileCacheProvider(CacheProvider):
    """File-based cache implementation."""

    def __init__(self, cache_dir: str = ".jules/cache") -> None:
        """Initialize the file cache.

        Args:
            cache_dir: Directory to store cache files.
        """
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(
                f"Failed to create cache directory {cache_dir}: {e}"
            )

    def _get_cache_path(self, key: str) -> Path:
        """Generate a safe file path for the cache key."""
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the file cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            expiry = data.get("expiry")
            if expiry and time.time() > expiry:
                self.delete(key)
                return None

            return data.get("value")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the file cache."""
        cache_path = self._get_cache_path(key)
        expiry = time.time() + ttl if ttl else None

        data = {
            "value": value,
            "expiry": expiry,
            "original_key_preview": key[:100]  # Store preview for debugging
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except (OSError, TypeError) as e:
            logger.warning(f"Failed to write cache key {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete a value from the file cache."""
        cache_path = self._get_cache_path(key)
        try:
            if cache_path.exists():
                cache_path.unlink()
        except OSError as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")
