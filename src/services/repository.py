"""File-based JSON implementation of the ProjectRepository protocol."""

from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from src.core.interfaces import ProjectRepository
from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class JsonProjectRepository(ProjectRepository[T], Generic[T]):
    """JSON file-based implementation of ProjectRepository."""

    def __init__(self, directory: str, model_class: type[T], id_getter: Callable[[T], str]):
        """Initialize the repository.

        Args:
        ----
            directory: The directory where JSON files will be stored.
            model_class: The Pydantic model class to deserialize into.
            id_getter: A callable that extracts the ID string from a model instance.

        """
        self.directory = Path(directory)
        self.model_class = model_class
        self.id_getter = id_getter

        try:
            self.directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RepositoryError(f"Failed to create repository directory {directory}: {e}") from e

    def _get_path(self, item_id: str) -> Path:
        """Get the file path for a given item ID."""
        # Sanitize the item_id just in case
        safe_id = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in item_id)
        return self.directory / f"{safe_id}.json"

    def save(self, item: T) -> None:
        """Save an item to the repository.

        Args:
        ----
            item: The domain model to save.

        Raises:
        ------
            RepositoryError: If saving fails.

        """
        try:
            item_id = self.id_getter(item)
            path = self._get_path(item_id)

            # Serialize the model safely
            content = item.model_dump_json(indent=2)

            # Write atomically to prevent data corruption
            fd, temp_path = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                os.replace(temp_path, path)
            except Exception as e:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e

            logger.debug(f"Saved {self.model_class.__name__} with ID {item_id} to {path}")
        except Exception as e:
            raise RepositoryError(f"Failed to save item: {e}") from e

    def get(self, item_id: str) -> T | None:
        """Retrieve an item from the repository by ID.

        Args:
        ----
            item_id: The unique identifier.

        Returns:
        -------
            The requested item, or None if not found.

        Raises:
        ------
            RepositoryError: If retrieval fails due to unexpected errors.

        """
        path = self._get_path(item_id)
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            return self.model_class.model_validate_json(content)
        except Exception as e:
            raise RepositoryError(f"Failed to retrieve item {item_id}: {e}") from e

    def get_all(self) -> list[T]:
        """Retrieve all items from the repository.

        Returns
        -------
            A list of all domain models.

        Raises
        ------
            RepositoryError: If retrieval fails.

        """
        items: list[T] = []
        try:
            if not self.directory.exists():
                return items

            for path in self.directory.glob("*.json"):
                if path.is_file():
                    try:
                        content = path.read_text(encoding="utf-8")
                        item = self.model_class.model_validate_json(content)
                        items.append(item)
                    except Exception as e:
                        logger.warning(f"Failed to load item from {path}: {e}")
                        # We log but continue loading other items
            return items
        except Exception as e:
            raise RepositoryError(f"Failed to retrieve all items: {e}") from e
