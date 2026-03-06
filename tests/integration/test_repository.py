"""Integration tests for ProjectRepository."""

import os
from pathlib import Path
from typing import Generator

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository


@pytest.fixture
def repo_file_path(tmp_path: Path) -> Generator[str, None, None]:
    """Provide a temporary file path for the repository."""
    file_path = str(tmp_path / ".test_jules_projects.json")
    yield file_path
    if os.path.exists(file_path):
        os.remove(file_path)


def test_repository_save_and_retrieve(repo_file_path: str) -> None:
    """Test that JsonProjectRepository correctly saves and retrieves WorkflowResult objects."""
    repo = JsonProjectRepository(file_path=repo_file_path, model_cls=WorkflowResult)

    # Initial state should be empty
    assert len(repo.get_all()) == 0

    # Create mock data
    idea_data = IdeaResponse(
        title="Test Idea",
        description="A great test idea.",
        slug="test-idea",
        tech_stack=["python", "pytest"],
        features=["feature1", "feature2"],
    )
    result = WorkflowResult(
        idea=idea_data,
        repo_url="https://github.com/test/test-idea",
        session_id="session-123",
        session_url="https://jules.google.com/sessions/session-123",
        pr_url="https://github.com/test/test-idea/pull/1",
    )

    # Save
    repo.save(result)

    # Retrieve and verify
    items = repo.get_all()
    assert len(items) == 1

    saved_item = items[0]
    assert saved_item.idea.title == "Test Idea"
    assert saved_item.repo_url == "https://github.com/test/test-idea"
    assert saved_item.session_id == "session-123"
    assert saved_item.session_url == "https://jules.google.com/sessions/session-123"
    assert saved_item.pr_url == "https://github.com/test/test-idea/pull/1"

    # Save another one
    result2 = WorkflowResult(
        idea=IdeaResponse(
            title="Idea 2",
            description="Another one",
            slug="idea-2",
            tech_stack=[],
            features=[]
        ),
        repo_url="https://github.com/test/idea-2"
    )
    repo.save(result2)

    # Retrieve and verify both
    items = repo.get_all()
    assert len(items) == 2
    assert items[1].idea.title == "Idea 2"
