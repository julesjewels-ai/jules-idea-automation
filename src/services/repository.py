"""Project repository implementation for the Jules Automation Tool."""

import json
import logging
from pathlib import Path
from typing import Optional, Any

from src.core.interfaces import ProjectRepository
from src.core.models import WorkflowResult
from src.utils.errors import RepositoryError

logger = logging.getLogger(__name__)


class JsonProjectRepository(ProjectRepository[WorkflowResult]):
    """File-based repository implementation using JSON."""

    def __init__(self, data_dir: str = ".jules_projects") -> None:
        """Initialize the JSON file repository.

        Args:
            data_dir: Directory to store project JSON files.
        """
        self.data_dir = Path(data_dir)
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create repository directory {data_dir}: {e}")

    def _get_path(self, slug: str) -> Path:
        """Generate a file path from a project slug."""
        return self.data_dir / f"{slug}.json"

    def save(self, result: WorkflowResult) -> None:
        """Save a project workflow result.

        Args:
            result: The WorkflowResult to save.
        """

        path = self._get_path(result.idea.slug)
        try:
            content = json.dumps(result.model_dump(), indent=2)
            path.write_text(content, encoding="utf-8")
            logger.debug(f"Saved project {result.idea.slug} to repository")
        except Exception as e:
            raise RepositoryError(f"Failed to save project {result.idea.slug} to {path}: {e}") from e

    def get_by_slug(self, slug: str) -> Optional[WorkflowResult]:
        """Retrieve a project by its slug.

        Args:
            slug: The project slug.

        Returns:
            The WorkflowResult if found, else None.
        """
        path = self._get_path(slug)
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
            return WorkflowResult.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to read project {slug} from repository: {e}")
            return None

    def list_all(self) -> list[WorkflowResult]:
        """List all saved projects.

        Returns:
            A list of all saved WorkflowResult objects.
        """
        results: list[WorkflowResult] = []
        if not self.data_dir.exists():
            return results

        for path in self.data_dir.glob("*.json"):
            try:
                content = path.read_text(encoding="utf-8")
                data = json.loads(content)
                results.append(WorkflowResult.model_validate(data))
            except Exception as e:
                logger.warning(f"Failed to load project from {path}: {e}")

        return results
