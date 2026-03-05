"""Repository implementation for data persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from src.core.interfaces import ProjectRepository
from src.core.models import WorkflowResult
from src.utils.errors import RepositoryError


class JsonProjectRepository(ProjectRepository[WorkflowResult]):
    """JSON file-based repository for WorkflowResult items."""

    def __init__(self, file_path: str | Path) -> None:
        """Initialize the repository.

        Args:
        ----
            file_path: Path to the JSON Lines file.

        """
        self.file_path = Path(file_path)

    def save(self, item: WorkflowResult) -> None:
        """Save a WorkflowResult to the repository.

        Uses atomic write by writing to a temporary file and swapping.

        Args:
        ----
            item: The WorkflowResult to save.

        Raises:
        ------
            RepositoryError: If the persistence operation fails.

        """
        try:
            # Prepare new data
            data_str = item.model_dump_json() + "\n"

            # Check if file exists to either append or create new
            if self.file_path.exists():
                # Read existing contents
                with open(self.file_path, "r", encoding="utf-8") as f:
                    existing = f.read()
                new_content = existing + data_str
            else:
                new_content = data_str

            # Create temp file in same directory
            parent_dir = self.file_path.parent
            parent_dir.mkdir(parents=True, exist_ok=True)

            fd, temp_path = tempfile.mkstemp(dir=parent_dir, prefix=".tmp_repo_")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                    temp_file.write(new_content)
                os.replace(temp_path, self.file_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        except Exception as e:
            raise RepositoryError(f"Failed to save item to repository: {e}") from e

    def get_all(self) -> list[WorkflowResult]:
        """Retrieve all WorkflowResult items from the repository.

        Returns
        -------
            A list of all persisted WorkflowResult items.

        Raises
        ------
            RepositoryError: If the retrieval operation fails.

        """
        if not self.file_path.exists():
            return []

        try:
            results = []
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        results.append(WorkflowResult(**data))
            return results
        except Exception as e:
            raise RepositoryError(f"Failed to retrieve items from repository: {e}") from e
