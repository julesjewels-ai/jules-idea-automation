import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository


@pytest.fixture
def temp_repo_dir() -> Generator[str, None, None]:
    """Provide a temporary directory for the repository tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def repo(temp_repo_dir: str) -> JsonProjectRepository[WorkflowResult]:
    """Provide a configured repository instance."""
    return JsonProjectRepository[WorkflowResult](
        base_dir=temp_repo_dir,
        model_class=WorkflowResult,
        id_getter=lambda res: res.idea.slug,
    )


def test_repository_save_and_get(repo: JsonProjectRepository[WorkflowResult]) -> None:
    """Test saving and retrieving an item from the repository."""
    result = WorkflowResult(
        idea=IdeaResponse(
            title="Test Idea",
            description="A test idea",
            slug="test-idea",
            tech_stack=["python", "pytest"],
            features=["testing"],
        ),
        repo_url="https://github.com/user/test-idea",
        session_id="session-123",
        session_url="https://jules.google.com/session/123",
    )

    repo.save(result)

    # Verify the item can be retrieved
    retrieved = repo.get("test-idea")
    assert retrieved is not None
    assert retrieved.idea.title == "Test Idea"
    assert retrieved.repo_url == "https://github.com/user/test-idea"
    assert retrieved.session_id == "session-123"


def test_repository_get_not_found(repo: JsonProjectRepository[WorkflowResult]) -> None:
    """Test retrieving a non-existent item returns None."""
    retrieved = repo.get("non-existent-idea")
    assert retrieved is None


def test_repository_list_all(repo: JsonProjectRepository[WorkflowResult]) -> None:
    """Test listing all items in the repository."""
    result1 = WorkflowResult(
        idea=IdeaResponse(
            title="Idea 1",
            description="First idea",
            slug="idea-1",
            tech_stack=[],
            features=[],
        ),
        repo_url="https://github.com/user/idea-1",
    )
    result2 = WorkflowResult(
        idea=IdeaResponse(
            title="Idea 2",
            description="Second idea",
            slug="idea-2",
            tech_stack=[],
            features=[],
        ),
        repo_url="https://github.com/user/idea-2",
    )

    repo.save(result1)
    repo.save(result2)

    items = repo.list_all()
    assert len(items) == 2
    slugs = {item.idea.slug for item in items}
    assert slugs == {"idea-1", "idea-2"}


def test_repository_atomic_write(temp_repo_dir: str, repo: JsonProjectRepository[WorkflowResult]) -> None:
    """Test that atomic writes prevent corrupted files from being created."""
    result = WorkflowResult(
        idea=IdeaResponse(
            title="Atomic Idea",
            description="Atomic testing",
            slug="atomic-idea",
            tech_stack=[],
            features=[],
        ),
        repo_url="https://github.com/user/atomic-idea",
    )

    repo.save(result)

    # Check that only the final .json file exists
    base_path = Path(temp_repo_dir)
    json_files = list(base_path.glob("*.json"))
    tmp_files = list(base_path.glob("*.tmp"))

    assert len(json_files) == 1
    assert json_files[0].name == "atomic-idea.json"
    assert len(tmp_files) == 0
