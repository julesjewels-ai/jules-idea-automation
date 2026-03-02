"""JSON file-based implementation of the ProjectRepository protocol."""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import TypeVar, Generic, Type, Any

from src.core.interfaces import ProjectRepository
from src.utils.errors import RepositoryError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class JsonProjectRepository(ProjectRepository[T], Generic[T]):
    """JSON file-based repository for persisting domain models."""

    def __init__(self, file_path: str, model_type: Type[T]) -> None:
        """Initialize the JSON repository.

        Args:
            file_path: Path to the JSON file where data is stored.
            model_type: The Pydantic model class to use for deserialization.
        """
        self.file_path = Path(file_path)
        self.model_type = model_type

        # Ensure parent directory exists
        if self.file_path.parent and str(self.file_path.parent) != ".":
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.warning(f"Failed to create repository directory {self.file_path.parent}: {e}")

        # Initialize an empty list in the file if it doesn't exist
        if not self.file_path.exists():
            self._write_data([])

    def _read_data(self) -> list[dict[str, Any]]:
        """Read data from the JSON file."""
        try:
            content = self.file_path.read_text(encoding="utf-8")
            if not content.strip():
                return []
            return json.loads(content)  # type: ignore[no-any-return]
        except (OSError, json.JSONDecodeError) as e:
            raise RepositoryError(f"Failed to read from repository {self.file_path}: {e}") from e

    def _write_data(self, data: list[dict[str, Any]]) -> None:
        """Write data to the JSON file using atomic writes."""
        try:
            fd, temp_path = tempfile.mkstemp(dir=self.file_path.parent, text=True)
            with os.fdopen(fd, 'w', encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.file_path)
        except OSError as e:
            # Clean up temp file if something fails before atomic swap
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise RepositoryError(f"Failed to write to repository {self.file_path}: {e}") from e

    def save(self, item: T) -> None:
        """Save an item to the repository.

        Args:
            item: The domain model instance to save.
        """
        data = self._read_data()
        data.append(item.model_dump())
        self._write_data(data)
        logger.debug(f"Saved {item.__class__.__name__} to {self.file_path}")

    def get_all(self) -> list[T]:
        """Retrieve all items from the repository.

        Returns:
            A list of all saved domain model instances.
        """
        data = self._read_data()
        results: list[T] = []
        for item_data in data:
            try:
                results.append(self.model_type.model_validate(item_data))
            except Exception as e:
                logger.warning(f"Failed to validate data as {self.model_type.__name__}: {e}")
        return results
