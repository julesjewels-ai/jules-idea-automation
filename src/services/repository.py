"""Repository implementation for persisting domain models."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generic, Type

from pydantic import BaseModel

from src.core.interfaces import T
from src.utils.errors import RepositoryError


class JsonProjectRepository(Generic[T]):
    """JSON file-based repository for persisting domain objects."""

    def __init__(self, file_path: str, model_cls: Type[T]) -> None:
        """Initialize the repository.

        Args:
        ----
            file_path: The path to the JSON file to store objects.
            model_cls: The Pydantic model class to deserialize objects into.

        """
        self.file_path = Path(file_path)
        self.model_cls = model_cls

    def save(self, item: T) -> None:
        """Save an item to the repository using atomic writes.

        Args:
        ----
            item: The domain object to persist.

        Raises:
        ------
            RepositoryError: If saving the item fails.

        """
        try:
            items = self._load_all_raw()

            # Use item.model_dump_json() to handle UUIDs, dates, etc., then parse back to dict
            # to append to our list of raw dictionaries
            if isinstance(item, BaseModel):
                item_dict = json.loads(item.model_dump_json())
            else:
                raise RepositoryError("Item must be a Pydantic model")

            items.append(item_dict)

            self._save_all_raw(items)
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to save item: {e}") from e

    def get_all(self) -> list[T]:
        """Retrieve all items from the repository.

        Returns
        -------
            A list of all persisted domain objects.

        Raises
        ------
            RepositoryError: If loading items fails.

        """
        try:
            raw_items = self._load_all_raw()
            return [self.model_cls(**item) for item in raw_items]
        except Exception as e:
            raise RepositoryError(f"Failed to get items: {e}") from e

    def _load_all_raw(self) -> list[dict[str, Any]]:
        """Load all items as raw dictionaries from the JSON file."""
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except json.JSONDecodeError:
            # File is corrupted or empty
            return []
        except Exception as e:
            raise RepositoryError(f"Failed to read repository file: {e}") from e

    def _save_all_raw(self, items: list[dict[str, Any]]) -> None:
        """Save all items as raw dictionaries using atomic writes."""
        directory = self.file_path.parent
        directory.mkdir(parents=True, exist_ok=True)

        try:
            # Atomic write
            fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".repo_", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2)

            # Atomically replace
            os.replace(temp_path, self.file_path)
        except Exception as e:
            # Cleanup temp file if error occurred before replace
            if "temp_path" in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise RepositoryError(f"Failed to write to repository file: {e}") from e
