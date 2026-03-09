"""Integration tests for JsonProjectRepository."""

import os
import shutil
import tempfile
from typing import Generator

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository


@pytest.fixture
def temp_repo_dir() -> Generator[str, None, None]:
    """Provide a temporary directory for repository testing."""
    temp_dir = tempfile.mkdtemp(prefix="jules_test_repo_")
    yield temp_dir
    shutil.rmtree(temp_dir)


def create_mock_result(slug: str) -> WorkflowResult:
    """Helper to create a mock WorkflowResult."""
    return WorkflowResult(
        idea=IdeaResponse(
            title=f"Test {slug}",
            description="A test idea",
            slug=slug,
            tech_stack=["python"],
            features=["feature 1"],
        ),
        repo_url=f"https://github.com/user/{slug}",
        session_id=f"session_{slug}",
        session_url=f"https://jules.google.com/session/{slug}",
    )


def test_repository_save_and_get(temp_repo_dir: str) -> None:
    """Test saving and retrieving an item."""
    repo = JsonProjectRepository[WorkflowResult](
        base_dir=temp_repo_dir,
        model_class=WorkflowResult,
        id_getter=lambda res: res.idea.slug,
    )

    mock_result = create_mock_result("test-idea")

    # Save the item
    repo.save(mock_result)

    # Verify file exists
    file_path = os.path.join(temp_repo_dir, "test-idea.json")
    assert os.path.exists(file_path)

    # Retrieve the item
    retrieved_result = repo.get("test-idea")
    assert retrieved_result is not None
    assert retrieved_result.idea.slug == "test-idea"
    assert retrieved_result.repo_url == "https://github.com/user/test-idea"


def test_repository_get_not_found(temp_repo_dir: str) -> None:
    """Test retrieving an item that doesn't exist."""
    repo = JsonProjectRepository[WorkflowResult](
        base_dir=temp_repo_dir,
        model_class=WorkflowResult,
        id_getter=lambda res: res.idea.slug,
    )

    retrieved_result = repo.get("non-existent")
    assert retrieved_result is None


def test_repository_list_all(temp_repo_dir: str) -> None:
    """Test listing all items in the repository."""
    repo = JsonProjectRepository[WorkflowResult](
        base_dir=temp_repo_dir,
        model_class=WorkflowResult,
        id_getter=lambda res: res.idea.slug,
    )

    # Repository should be empty initially
    assert len(repo.list_all()) == 0

    # Save multiple items
    repo.save(create_mock_result("idea-1"))
    repo.save(create_mock_result("idea-2"))
    repo.save(create_mock_result("idea-3"))

    # List all items
    all_items = repo.list_all()
    assert len(all_items) == 3

    slugs = {item.idea.slug for item in all_items}
    assert slugs == {"idea-1", "idea-2", "idea-3"}
