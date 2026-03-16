"""Repository implementation for data persistence."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Callable, Generic, TypeVar

from pydantic import BaseModel

from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)

# T must be a subclass of BaseModel for type-safe deserialization
T = TypeVar("T", bound=BaseModel)


class JsonProjectRepository(Generic[T]):
    """File-based implementation of the generic repository.

    Uses atomic file writes to prevent data corruption.
    """

    def __init__(self, base_dir: str, model_class: type[T], id_getter: Callable[[T], str]):
        """Initialize the repository.

        Args:
        ----
            base_dir: Directory to store JSON files.
            model_class: Pydantic model class for type-safe deserialization.
            id_getter: Callable to extract the unique ID from a model instance.

        """
        self.base_dir = Path(base_dir)
        self.model_class = model_class
        self.id_getter = id_getter

        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create repository directory {self.base_dir}: {e}")

    def _get_file_path(self, item_id: str) -> Path:
        """Get the file path for an item ID."""
        # Clean ID to prevent path traversal
        clean_id = "".join(c for c in item_id if c.isalnum() or c in ("-", "_"))
        return self.base_dir / f"{clean_id}.json"

    def save(self, item: T) -> None:
        """Save the item to a JSON file.

        Uses tempfile and os.replace for atomic writes.
        """
        try:
            item_id = self.id_getter(item)
            file_path = self._get_file_path(item_id)

            # model_dump_json serializes UUIDs, dates correctly
            json_data = item.model_dump_json(indent=2).encode("utf-8")

            # Write to a temp file in the same directory, then atomically replace
            dir_ = str(self.base_dir)
            fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".json.tmp")
            try:
                os.write(fd, json_data)
            finally:
                os.close(fd)

            os.replace(tmp_path, file_path)
            logger.debug(f"Saved item {item_id} to {file_path}")

        except Exception as e:
            raise RepositoryError(f"Failed to save item: {e}") from e

    def get(self, id: str) -> T | None:
        """Retrieve the item by its unique ID."""
        file_path = self._get_file_path(id)
        if not file_path.exists():
            return None

        try:
            json_str = file_path.read_text(encoding="utf-8")
            return self.model_class.model_validate_json(json_str)
        except Exception as e:
            logger.error(f"Failed to retrieve item {id} from {file_path}: {e}")
            raise RepositoryError(f"Failed to retrieve item {id}: {e}") from e

    def list_all(self) -> list[T]:
        """List all items in the repository."""
        items: list[T] = []
        if not self.base_dir.exists():
            return items

        for file_path in self.base_dir.glob("*.json"):
            try:
                json_str = file_path.read_text(encoding="utf-8")
                item = self.model_class.model_validate_json(json_str)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to load item from {file_path}: {e}")
                # Continue loading other files even if one is corrupted

        return items
