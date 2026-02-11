"""Cache implementation service."""

import hashlib
import json
import logging
import os
from typing import Any, Optional

from src.utils.errors import CacheError

logger = logging.getLogger(__name__)


class FileCacheProvider:
    """File-based implementation of CacheProvider."""

    def __init__(self, cache_dir: str = ".jules/cache") -> None:
        """Initialize the cache provider.

        Args:
            cache_dir: Directory to store cache files.
        """
        self.cache_dir = cache_dir
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            raise CacheError(f"Failed to create cache directory: {e}")

    def _get_path(self, key: str) -> str:
        """Generate a file path for the given key."""
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        path = self._get_path(key)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to read cache for key {key}: {e}")
                return None
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        path = self._get_path(key)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(value, f)
        except (TypeError, OSError) as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")
