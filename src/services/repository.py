"""File-based repository implementation for the Jules Automation Tool."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Generic

from pydantic import BaseModel

from src.core.interfaces import T
from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)


class JsonProjectRepository(Generic[T]):
    """JSON file-based implementation of ProjectRepository.

    This repository stores each item as a separate JSON file in a designated directory.
    """

    def __init__(self, base_dir: str | Path, model_class: Any, id_getter: Callable[[T], str]) -> None:
        """Initialize the JSON repository.

        Args:
        ----
            base_dir: Directory where JSON files will be stored.
            model_class: Pydantic BaseModel class for deserialization.
            id_getter: Function to extract a unique ID from an item.

        """
        self.base_dir = Path(base_dir)
        self.model_class = model_class
        self.id_getter = id_getter

        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RepositoryError(f"Failed to create repository directory {self.base_dir}: {e}") from e

    def _get_file_path(self, item_id: str) -> Path:
        """Get the file path for a given item ID."""
        return self.base_dir / f"{item_id}.json"

    def save(self, item: T) -> None:
        """Save an item to the repository.

        Args:
        ----
            item: The domain model to save.

        """
        if not isinstance(item, BaseModel):
            raise RepositoryError(f"Item must be a Pydantic BaseModel, got {type(item)}")

        item_id = self.id_getter(item)
        file_path = self._get_file_path(item_id)

        try:
            # model_dump_json serializes types like UUID and datetime safely
            json_data = item.model_dump_json()

            # Atomic write
            fd, tmp_path = tempfile.mkstemp(dir=str(self.base_dir), suffix=".json.tmp")
            try:
                os.write(fd, json_data.encode("utf-8"))
            finally:
                os.close(fd)
            os.replace(tmp_path, file_path)

            logger.debug(f"Saved item {item_id} to {file_path}")
        except Exception as e:
            raise RepositoryError(f"Failed to save item {item_id} to {file_path}: {e}") from e

    def get(self, item_id: str) -> T | None:
        """Retrieve an item by its unique identifier.

        Args:
        ----
            item_id: The unique identifier.

        Returns:
        -------
            The domain model if found, None otherwise.

        """
        file_path = self._get_file_path(item_id)
        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            # Pydantic validation and instantiation
            model_instance = self.model_class(**data)
            return model_instance  # type: ignore[no-any-return]
        except Exception as e:
            raise RepositoryError(f"Failed to retrieve item {item_id} from {file_path}: {e}") from e

    def list_all(self) -> list[T]:
        """List all items in the repository.

        Returns
        -------
            A list of all domain models.

        """
        items: list[T] = []
        try:
            for file_path in self.base_dir.glob("*.json"):
                # Use stem as item_id, although get() takes the ID
                item_id = file_path.stem
                item = self.get(item_id)
                if item is not None:
                    items.append(item)
        except Exception as e:
            raise RepositoryError(f"Failed to list items from {self.base_dir}: {e}") from e

        return items
