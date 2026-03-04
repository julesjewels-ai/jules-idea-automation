"""JSON file-based implementation of the ProjectRepository."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from src.core.interfaces import ProjectRepository
from src.utils.errors import RepositoryError

T = TypeVar("T", bound=BaseModel)


class JsonProjectRepository(ProjectRepository[T], Generic[T]):
    """JSON file-based implementation of ProjectRepository.

    Persists BaseModel objects to a JSONL file using atomic writes.
    """

    def __init__(self, file_path: str, model_class: type[T]) -> None:
        """Initialize the JSON repository.

        Args:
        ----
            file_path: Path to the JSONL file.
            model_class: The Pydantic model class to use for deserialization.

        """
        self.file_path = Path(file_path)
        self.model_class = model_class

        # Ensure directory exists
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                self.file_path.touch()
        except OSError as e:
            raise RepositoryError(f"Failed to initialize repository at {self.file_path}: {e}")

    def save(self, model: T) -> None:
        """Save a domain model to the JSONL file using an atomic write.

        Args:
        ----
            model: The domain model to persist.

        Raises:
        ------
            RepositoryError: If saving fails.

        """
        try:
            # Read existing lines
            lines = []
            if self.file_path.exists():
                lines = self.file_path.read_text(encoding="utf-8").splitlines()

            # Append the new model
            lines.append(model.model_dump_json())

            # Write atomically to temporary file and replace
            fd, temp_path = tempfile.mkstemp(dir=self.file_path.parent, prefix=".tmp_repo_")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    for line in lines:
                        if line.strip():
                            f.write(f"{line}\n")

                os.replace(temp_path, self.file_path)
            except Exception as e:
                # Clean up temp file on failure
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise e

        except Exception as e:
            raise RepositoryError(f"Failed to save model to repository: {e}")

    def get_all(self) -> list[T]:
        """Retrieve all persisted domain models.

        Returns
        -------
            A list of all saved models.

        Raises
        ------
            RepositoryError: If retrieval fails.

        """
        try:
            if not self.file_path.exists():
                return []

            lines = self.file_path.read_text(encoding="utf-8").splitlines()
            models = []

            for line in lines:
                if line.strip():
                    try:
                        data = json.loads(line)
                        models.append(self.model_class.model_validate(data))
                    except (json.JSONDecodeError, ValueError) as e:
                        # Log warning, but continue loading valid ones
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.warning(f"Failed to parse repository entry: {e}")

            return models
        except Exception as e:
            raise RepositoryError(f"Failed to retrieve models from repository: {e}")
