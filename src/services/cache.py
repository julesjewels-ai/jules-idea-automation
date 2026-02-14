"""Cache service implementation."""

import hashlib
import json
import logging
import os
import shutil
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from src.core.interfaces import CacheProvider


logger = logging.getLogger(__name__)

T = TypeVar("T")


class FileCacheProvider:
    """File-based implementation of CacheProvider."""

    def __init__(self, cache_dir: str = ".jules/cache") -> None:
        """Initialize the file cache provider.

        Args:
            cache_dir: Directory to store cache files.
        """
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_filepath(self, key: str) -> str:
        """Get the file path for a given key."""
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        filepath = self._get_filepath(key)
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache file {filepath}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        filepath = self._get_filepath(key)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(value, f)
        except (TypeError, OSError) as e:
            logger.error(f"Failed to write cache file {filepath}: {e}")

    def delete(self, key: str) -> None:
        """Remove a value from the cache."""
        filepath = self._get_filepath(key)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                logger.error(f"Failed to delete cache file {filepath}: {e}")

    def clear(self) -> None:
        """Clear all cached values."""
        if os.path.exists(self.cache_dir):
            try:
                shutil.rmtree(self.cache_dir)
                self._ensure_cache_dir()
            except OSError as e:
                logger.error(
                    f"Failed to clear cache directory {self.cache_dir}: {e}"
                )


def smart_cache(
    key_builder: Callable[..., str]
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to cache method results using a key builder.

    Args:
        key_builder: A function that takes the instance (self) and method
                     arguments and returns a unique string key.

    Returns:
        The decorated method.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            # Check if instance has a cache provider
            cache: Optional[CacheProvider] = getattr(self, "cache", None)
            if not cache:
                return func(self, *args, **kwargs)

            try:
                key = key_builder(self, *args, **kwargs)
                cached_value = cache.get(key)

                if cached_value is not None:
                    logger.info(f"Cache hit for key: {key}")
                    return cached_value  # type: ignore

                logger.info(f"Cache miss for key: {key}")
                result = func(self, *args, **kwargs)
                cache.set(key, result)
                return result
            except Exception as e:
                logger.warning(f"Cache error in wrapper: {e}")
                return func(self, *args, **kwargs)

        return wrapper
    return decorator
