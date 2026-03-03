"""Concrete implementations of the ProjectRepository protocol."""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from src.core.interfaces import ProjectRepository
from src.core.models import WorkflowResult
from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)


class JsonProjectRepository(ProjectRepository[WorkflowResult]):
    """JSON file-based implementation of the ProjectRepository."""

    def __init__(self, data_dir: str = ".jules_data") -> None:
        """Initialize the JSON repository.

        Args:
            data_dir: The directory to store data files.
        """
        self.data_dir = Path(data_dir)

        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create repository directory {self.data_dir}: {e}")

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a specific key."""
        return self.data_dir / f"{key}.json"

    def save(self, item: WorkflowResult) -> None:
        """Save a WorkflowResult to a JSON file.

        Args:
            item: The WorkflowResult to save.

        Raises:
            RepositoryError: If saving fails.
        """
        key = item.idea.slug
        file_path = self._get_file_path(key)

        try:
            # We must use ignore[no-any-return] here if needed for model_dump,
            # but model_dump returns dict[str, Any] usually
            data = item.model_dump()

            # Use atomic write: write to temp file, then rename
            fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix=f".{key}_", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                # Atomic replace
                os.replace(temp_path, file_path)
                logger.debug(f"Successfully saved WorkflowResult to {file_path}")
            except Exception as e:
                # Clean up temp file on failure
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise e

        except Exception as e:
            raise RepositoryError(f"Failed to save WorkflowResult for key {key}: {e}") from e

    def get(self, key: str) -> Optional[WorkflowResult]:
        """Retrieve a WorkflowResult by its slug.

        Args:
            key: The unique key (slug) of the workflow result.

        Returns:
            The WorkflowResult if found, or None.

        Raises:
            RepositoryError: If an error occurs reading the file.
        """
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WorkflowResult(**data)
        except Exception as e:
            raise RepositoryError(f"Failed to load WorkflowResult from {file_path}: {e}") from e

    def list_all(self) -> list[WorkflowResult]:
        """List all WorkflowResults in the repository.

        Returns:
            A list of all found WorkflowResults.

        Raises:
            RepositoryError: If an error occurs reading the directory or files.
        """
        results: list[WorkflowResult] = []
        if not self.data_dir.exists():
            return results

        try:
            for file_path in self.data_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    results.append(WorkflowResult(**data))
                except Exception as e:
                    logger.warning(f"Skipping invalid data file {file_path}: {e}")
                    # We continue loading other valid files

            return results
        except Exception as e:
            raise RepositoryError(f"Failed to list WorkflowResults from {self.data_dir}: {e}") from e
