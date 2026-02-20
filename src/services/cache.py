"""Cache provider implementations."""

from __future__ import annotations

import json
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

from src.core.interfaces import CacheProvider


logger = logging.getLogger(__name__)


class FileCacheProvider(CacheProvider):
    """A simple file-based cache provider."""

    def __init__(self, cache_dir: str = ".cache/gemini") -> None:
        """Initialize the cache provider.

        Args:
            cache_dir: The directory to store cache files.
        """
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create cache directory {cache_dir}: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """Generate a safe file path for the given key."""
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Retrieve a value from the cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache for key {key}: {e}")
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a value in the cache."""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        cache_path = self._get_cache_path(key)
        try:
            if cache_path.exists():
                cache_path.unlink()
        except OSError as e:
            logger.warning(f"Failed to delete cache for key {key}: {e}")
