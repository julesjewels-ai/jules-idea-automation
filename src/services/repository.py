"""Repository implementations for the Jules Automation Tool."""

from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from src.core.interfaces import ProjectRepository
from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class JsonProjectRepository(ProjectRepository[T]):
    """JSON file-based repository implementation.

    Uses atomic writes to prevent data corruption.
    """

    def __init__(
        self,
        model_class: type[T],
        base_dir: Path,
        id_getter: Callable[[T], str],
    ) -> None:
        """Initialize the repository.

        Args:
        ----
            model_class: Pydantic model type for deserialization.
            base_dir: Directory where JSON files will be stored.
            id_getter: Function to extract unique ID from the domain model.

        """
        self.model_class = model_class
        self.base_dir = Path(base_dir)
        self.id_getter = id_getter

        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RepositoryError(f"Failed to create repository directory: {e}") from e

    def _get_file_path(self, item_id: str) -> Path:
        """Get the file path for a specific item ID."""
        safe_id = item_id.replace("/", "_").replace("\\", "_")
        return self.base_dir / f"{safe_id}.json"

    def save(self, item: T) -> None:
        """Save an item to a JSON file using an atomic write.

        Args:
        ----
            item: The Pydantic model to save.

        Raises:
        ------
            RepositoryError: If saving fails.

        """
        temp_path = None
        try:
            item_id = self.id_getter(item)
            file_path = self._get_file_path(item_id)

            json_data = item.model_dump_json(indent=2)

            fd, temp_path = tempfile.mkstemp(dir=self.base_dir, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(json_data)

            os.replace(temp_path, file_path)
            logger.debug(f"Saved {self.model_class.__name__} {item_id} to {file_path}")

        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            logger.error(f"Failed to save {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to save item: {e}") from e

    def get(self, item_id: str) -> T | None:
        """Retrieve an item from its JSON file.

        Args:
        ----
            item_id: The unique identifier.

        Returns:
        -------
            The Pydantic model instance, or None if not found.

        Raises:
        ------
            RepositoryError: If file read or validation fails.

        """
        file_path = self._get_file_path(item_id)
        if not file_path.exists():
            return None

        try:
            json_data = file_path.read_text(encoding="utf-8")
            return self.model_class.model_validate_json(json_data)
        except Exception as e:
            logger.error(f"Failed to load {self.model_class.__name__} {item_id}: {e}")
            raise RepositoryError(f"Failed to load item {item_id}: {e}") from e

    def list_all(self) -> list[T]:
        """Retrieve all items from the directory.

        Returns
        -------
            List of Pydantic model instances.

        Raises
        ------
            RepositoryError: If directory read or validation fails.

        """
        items: list[T] = []
        try:
            for file_path in self.base_dir.glob("*.json"):
                try:
                    json_data = file_path.read_text(encoding="utf-8")
                    item = self.model_class.model_validate_json(json_data)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Skipping malformed file {file_path}: {e}")
        except Exception as e:
            raise RepositoryError(f"Failed to list items: {e}") from e

        return items
