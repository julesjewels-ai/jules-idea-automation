"""Integration tests for JsonProjectRepository."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository
from src.utils.errors import RepositoryError


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Yield a temporary directory for repository testing."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def repository(temp_dir: Path) -> JsonProjectRepository[WorkflowResult]:
    """Fixture to provide a JsonProjectRepository."""
    return JsonProjectRepository[WorkflowResult](
        model_class=WorkflowResult,
        base_dir=temp_dir,
        id_getter=lambda item: item.idea.slug,
    )


def _create_mock_result(slug: str) -> WorkflowResult:
    """Helper to create a mock WorkflowResult."""
    return WorkflowResult(
        idea=IdeaResponse(
            title="Test Idea",
            description="Test Description",
            slug=slug,
            tech_stack=["python"],
            features=["feature 1"],
        ),
        repo_url=f"https://github.com/user/{slug}",
        session_id=f"session-{slug}",
        session_url=f"http://example.com/{slug}",
    )


def test_save_and_get(repository: JsonProjectRepository[WorkflowResult], temp_dir: Path) -> None:
    """Test saving and retrieving an item."""
    result = _create_mock_result("test-slug")

    repository.save(result)

    # Assert file was created
    file_path = temp_dir / "test-slug.json"
    assert file_path.exists()

    # Assert retrieval
    retrieved = repository.get("test-slug")
    assert retrieved is not None
    assert retrieved.idea.slug == "test-slug"
    assert retrieved.repo_url == "https://github.com/user/test-slug"


def test_list_all(repository: JsonProjectRepository[WorkflowResult]) -> None:
    """Test retrieving all items."""
    result1 = _create_mock_result("test-slug-1")
    result2 = _create_mock_result("test-slug-2")

    repository.save(result1)
    repository.save(result2)

    items = repository.list_all()
    assert len(items) == 2

    slugs = {item.idea.slug for item in items}
    assert slugs == {"test-slug-1", "test-slug-2"}


def test_get_not_found(repository: JsonProjectRepository[WorkflowResult]) -> None:
    """Test getting an item that doesn't exist."""
    retrieved = repository.get("non-existent-slug")
    assert retrieved is None


def test_save_error_read_only_dir(temp_dir: Path) -> None:
    """Test repository save error handling."""
    read_only_dir = temp_dir / "readonly"
    read_only_dir.mkdir()
    read_only_dir.chmod(0o555)  # Read and execute, no write

    repository = JsonProjectRepository[WorkflowResult](
        model_class=WorkflowResult,
        base_dir=read_only_dir,
        id_getter=lambda item: item.idea.slug,
    )

    result = _create_mock_result("test-slug")

    with pytest.raises(RepositoryError, match="Failed to save item"):
        repository.save(result)

    # Restore permissions for clean up
    read_only_dir.chmod(0o777)
