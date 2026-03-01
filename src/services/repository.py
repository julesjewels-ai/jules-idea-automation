"""Data repository implementation using JSON lines for the Jules Automation Tool."""

import json
import logging
from pathlib import Path
from typing import TypeVar, Generic, Type, Optional

from pydantic import BaseModel

from src.core.interfaces import ProjectRepository
from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class JsonProjectRepository(ProjectRepository[T], Generic[T]):
    """JSON implementation of ProjectRepository.

    Persists Pydantic models to a JSON Lines file.
    """

    def __init__(self, file_path: str, model_type: Type[T]) -> None:
        """Initialize the JSON repository.

        Args:
            file_path: The path to the JSON Lines file.
            model_type: The Pydantic model type to persist.
        """
        self.file_path = Path(file_path)
        self.model_type = model_type

        # Ensure directory exists
        if not self.file_path.parent.exists():
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise RepositoryError(
                    f"Failed to create repository directory: {e}",
                    tip="Check directory permissions."
                )

        # Ensure file exists
        if not self.file_path.exists():
            try:
                self.file_path.touch()
            except Exception as e:
                raise RepositoryError(
                    f"Failed to create repository file: {e}",
                    tip="Check file permissions."
                )

    def _get_item_id(self, item: T) -> str:
        """Extract the ID from an item.

        Assumes the item has an 'id' or 'slug' field, or nested 'idea.slug'.
        Raises RepositoryError if a stable ID cannot be determined.
        """
        item_dict = item.model_dump()

        if 'id' in item_dict and item_dict['id']:
            return str(item_dict['id'])

        if 'idea' in item_dict and isinstance(item_dict['idea'], dict) and 'slug' in item_dict['idea']:
            return str(item_dict['idea']['slug'])

        if 'slug' in item_dict and item_dict['slug']:
            return str(item_dict['slug'])

        raise RepositoryError(
            "Could not determine a stable ID for the domain model.",
            tip="Ensure the model has an 'id' or 'slug' attribute."
        )

    def save(self, item: T) -> None:
        """Save an item to the repository.

        Args:
            item: The domain model to save.

        Raises:
            RepositoryError: If saving fails.
        """
        item_id = self._get_item_id(item)
        logger.debug(f"Saving item with ID: {item_id}")

        items = self.list_all()

        # Check if item exists, if so update it
        found = False
        for i, existing_item in enumerate(items):
            if self._get_item_id(existing_item) == item_id:
                items[i] = item
                found = True
                break

        if not found:
            items.append(item)

        self._write_all(items)

    def get(self, item_id: str) -> Optional[T]:
        """Retrieve an item from the repository.

        Args:
            item_id: The unique identifier of the item.

        Returns:
            The retrieved item, or None if not found.

        Raises:
            RepositoryError: If reading fails.
        """
        items = self.list_all()
        for item in items:
            if self._get_item_id(item) == item_id:
                return item
        return None

    def list_all(self) -> list[T]:
        """List all items in the repository.

        Returns:
            A list of all items in the repository.

        Raises:
            RepositoryError: If reading or parsing fails.
        """
        try:
            if not self.file_path.exists():
                return []

            content = self.file_path.read_text(encoding='utf-8')
            if not content.strip():
                return []

            items: list[T] = []
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    items.append(self.model_type.model_validate(data))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON line: {line[:50]}...")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to validate model: {e}")
                    continue

            return items
        except Exception as e:
            raise RepositoryError(
                f"Failed to read from repository: {e}",
                tip="Check file permissions and format."
            )

    def _write_all(self, items: list[T]) -> None:
        """Write all items back to the JSON Lines file using atomic writes."""
        import tempfile
        import os

        try:
            fd, temp_path = tempfile.mkstemp(dir=str(self.file_path.parent))

            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(item.model_dump_json() + '\n')

            os.replace(temp_path, self.file_path)

        except Exception as e:
            raise RepositoryError(
                f"Failed to write to repository: {e}",
                tip="Check file permissions and disk space."
            )
