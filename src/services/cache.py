import os
import json
import hashlib
import logging
from typing import Any, Optional
from src.core.interfaces import CacheProvider

logger = logging.getLogger(__name__)

class FileCacheProvider(CacheProvider):
    """File-based implementation of CacheProvider."""

    def __init__(self, cache_dir: str = ".cache/gemini"):
        self.cache_dir = cache_dir
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create cache directory {self.cache_dir}: {e}")

    def _get_path(self, key: str) -> str:
        """Generate a file path for the given cache key."""
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        path = self._get_path(key)
        try:
            with open(path, 'w') as f:
                json.dump(value, f)
        except Exception as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        path = self._get_path(key)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to delete cache for key {key}: {e}")
