"""Repository implementation for data persistence."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from src.core.interfaces import ProjectRepository
from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)

# T must be a Pydantic model so we can call model_dump_json() and model_validate()
T = TypeVar("T", bound=BaseModel)


class JsonProjectRepository(ProjectRepository[T]):
    """JSON file-based implementation of the ProjectRepository protocol."""

    def __init__(self, file_path: str, model_class: type[T], id_getter: Callable[[T], str]) -> None:
        """Initialize the JSON repository.

        Args:
        ----
            file_path: The path to the JSON file where items will be stored.
            model_class: The Pydantic model class to deserialize into.
            id_getter: A callable that takes an item and returns its unique identifier.

        """
        self.file_path = Path(file_path)
        self.model_class = model_class
        self.id_getter = id_getter

        # Ensure directory exists
        if self.file_path.parent and str(self.file_path.parent) != ".":
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.warning(f"Failed to create repository directory {self.file_path.parent}: {e}")

    def _load_data(self) -> dict[str, Any]:
        """Load the raw JSON data from the file."""
        if not self.file_path.exists():
            return {}
        try:
            content = self.file_path.read_text(encoding="utf-8")
            if not content.strip():
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                logger.warning(f"Expected dict in {self.file_path}, got {type(data)}. Returning empty dict.")
                return {}
            return data
        except Exception as e:
            raise RepositoryError(f"Failed to read from repository file {self.file_path}: {e}") from e

    def save(self, item: T) -> None:
        """Save an item to the repository using an atomic write."""
        try:
            item_id = self.id_getter(item)
            data = self._load_data()

            # We use model_dump_json() to safely handle UUIDs, dates, etc., then parse it back to a dict
            # so we can store it in the aggregate JSON dict.
            item_dict = json.loads(item.model_dump_json())
            data[item_id] = item_dict

            self._atomic_write(data)
            logger.debug(f"Saved item {item_id} to repository {self.file_path}")
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to save item to repository: {e}") from e

    def get(self, id: str) -> T | None:
        """Retrieve an item by its unique identifier."""
        try:
            data = self._load_data()
            item_data = data.get(id)
            if not item_data:
                return None
            return self.model_class.model_validate(item_data)
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to retrieve item {id} from repository: {e}") from e

    def get_all(self) -> list[T]:
        """Retrieve all items from the repository."""
        try:
            data = self._load_data()
            items = []
            for item_data in data.values():
                items.append(self.model_class.model_validate(item_data))
            return items
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to retrieve items from repository: {e}") from e

    def _atomic_write(self, data: dict[str, Any]) -> None:
        """Write data to the file atomically."""
        tmp_path = None
        try:
            json_str = json.dumps(data, indent=2) + "\n"
            content = json_str.encode("utf-8")

            dir_ = str(self.file_path.parent)
            fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".json.tmp")
            try:
                os.write(fd, content)
            finally:
                os.close(fd)
            os.replace(tmp_path, self.file_path)
        except Exception as e:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise RepositoryError(f"Atomic write to {self.file_path} failed: {e}") from e
