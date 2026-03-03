"""Integration tests for the ProjectRepository implementation."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator, Any

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository
from src.utils.errors import RepositoryError


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Provides a temporary directory for repository storage."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def repository(temp_dir: str) -> JsonProjectRepository:
    """Provides a configured JsonProjectRepository instance."""
    return JsonProjectRepository(data_dir=temp_dir)


@pytest.fixture
def sample_workflow_result() -> WorkflowResult:
    """Provides a sample WorkflowResult for testing."""
    idea = IdeaResponse(
        title="Test Idea",
        description="A great test idea",
        slug="test-idea",
        tech_stack=["python", "pytest"],
        features=["feature1", "feature2"]
    )
    return WorkflowResult(
        idea=idea,
        repo_url="https://github.com/user/test-idea",
        session_id="session-123",
        session_url="https://jules.google.com/session-123",
        pr_url="https://github.com/user/test-idea/pull/1"
    )


def test_repository_save_and_get(repository: JsonProjectRepository, sample_workflow_result: WorkflowResult) -> None:
    """Test full roundtrip: saving and retrieving an item."""
    # Ensure it's not there initially
    assert repository.get(sample_workflow_result.idea.slug) is None

    # Save the item
    repository.save(sample_workflow_result)

    # Check that a file was created
    file_path = Path(repository.data_dir) / f"{sample_workflow_result.idea.slug}.json"
    assert file_path.exists()

    # Retrieve the item
    retrieved = repository.get(sample_workflow_result.idea.slug)
    assert retrieved is not None

    # Validate the contents match
    assert retrieved.idea.title == sample_workflow_result.idea.title
    assert retrieved.idea.slug == sample_workflow_result.idea.slug
    assert retrieved.repo_url == sample_workflow_result.repo_url
    assert retrieved.session_id == sample_workflow_result.session_id


def test_repository_list_all(repository: JsonProjectRepository, sample_workflow_result: WorkflowResult) -> None:
    """Test listing all saved items."""
    # List should be empty initially
    assert len(repository.list_all()) == 0

    # Save one item
    repository.save(sample_workflow_result)

    # Create and save a second item
    idea2 = IdeaResponse(
        title="Second Idea",
        description="Another test idea",
        slug="second-idea",
        tech_stack=[],
        features=[]
    )
    result2 = WorkflowResult(
        idea=idea2,
        repo_url="https://github.com/user/second-idea"
    )
    repository.save(result2)

    # Retrieve all items
    all_results = repository.list_all()
    assert len(all_results) == 2

    # Verify both items are in the list
    slugs = [r.idea.slug for r in all_results]
    assert "test-idea" in slugs
    assert "second-idea" in slugs


def test_repository_handles_corrupt_data(repository: JsonProjectRepository, sample_workflow_result: WorkflowResult) -> None:
    """Test that the repository handles corrupted JSON gracefully during list_all."""
    # Save a valid item
    repository.save(sample_workflow_result)

    # Create a corrupt file directly
    corrupt_path = Path(repository.data_dir) / "corrupt-idea.json"
    with open(corrupt_path, "w", encoding="utf-8") as f:
        f.write("{ invalid json")

    # List all should still return the valid item and skip the corrupt one
    results = repository.list_all()
    assert len(results) == 1
    assert results[0].idea.slug == sample_workflow_result.idea.slug


def test_repository_save_failure(repository: JsonProjectRepository, sample_workflow_result: WorkflowResult, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that RepositoryError is raised on save failure."""
    def mock_dump(*args: Any, **kwargs: Any) -> None:
        raise OSError("Simulated write failure")

    import json
    monkeypatch.setattr(json, "dump", mock_dump)

    with pytest.raises(RepositoryError) as exc_info:
        repository.save(sample_workflow_result)

    assert exc_info.value is not None
    assert "Failed to save WorkflowResult" in str(exc_info.value)
