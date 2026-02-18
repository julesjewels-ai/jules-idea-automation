"""File-based caching implementation."""

import os
import json
import hashlib
import time
import logging
from typing import Optional, Any
from src.core.interfaces import CacheProvider

logger = logging.getLogger(__name__)


class FileCacheProvider(CacheProvider):
    """File-system based cache implementation."""

    def __init__(self, cache_dir: str = ".cache") -> None:
        """Initialize the cache provider.

        Args:
            cache_dir: Directory to store cache files.
        """
        self.cache_dir = cache_dir
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create cache directory {cache_dir}: {e}")

    def _get_path(self, key: str) -> str:
        """Generate a safe file path for the key."""
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        filepath = self._get_path(key)
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check TTL if present
            ttl = data.get('ttl')
            timestamp = data.get('timestamp')

            if ttl and timestamp:
                age = time.time() - timestamp
                if age > ttl:
                    self.delete(key)
                    return None

            return data.get('value')

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value in the cache."""
        filepath = self._get_path(key)
        data = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except OSError as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")

    def delete(self, key: str) -> None:
        """Remove a value from the cache."""
        filepath = self._get_path(key)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError as e:
            logger.warning(f"Failed to delete cache for key {key}: {e}")
