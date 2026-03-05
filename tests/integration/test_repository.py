"""Integration tests for ProjectRepository."""

import json
import os
import tempfile
from collections.abc import Generator

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository


@pytest.fixture
def temp_repo_path() -> Generator[str, None, None]:
    """Yield a temporary file path for the repository."""
    fd, path = tempfile.mkstemp(suffix=".jsonl", prefix="test_repo_")
    os.close(fd)

    yield path

    if os.path.exists(path):
        os.remove(path)


def test_json_project_repository_integration(temp_repo_path: str) -> None:
    """Test full cycle of save and get_all for JsonProjectRepository."""
    # Ensure file starts empty
    with open(temp_repo_path, "w", encoding="utf-8") as f:
        f.write("")

    repo = JsonProjectRepository(temp_repo_path)

    # Verify initial empty state
    assert len(repo.get_all()) == 0

    # Create first item
    idea1 = IdeaResponse(
        title="App One",
        description="First description",
        slug="app-one",
        tech_stack=["python"],
        features=["feature1"],
    )
    result1 = WorkflowResult(
        idea=idea1,
        repo_url="https://github.com/user/app-one",
        session_id="ses-123",
    )

    # Save first item
    repo.save(result1)

    # Verify first item saved correctly
    items = repo.get_all()
    assert len(items) == 1
    assert items[0].idea.title == "App One"
    assert items[0].session_id == "ses-123"

    # Create second item
    idea2 = IdeaResponse(
        title="App Two",
        description="Second description",
        slug="app-two",
        tech_stack=["rust"],
        features=[],
    )
    result2 = WorkflowResult(
        idea=idea2,
        repo_url="https://github.com/user/app-two",
        session_id="ses-456",
        session_url="https://jules.app/ses-456",
        pr_url="https://github.com/user/app-two/pull/1",
    )

    # Save second item
    repo.save(result2)

    # Verify both items saved correctly
    items = repo.get_all()
    assert len(items) == 2
    assert items[0].idea.title == "App One"
    assert items[1].idea.title == "App Two"
    assert items[1].session_url == "https://jules.app/ses-456"
    assert items[1].pr_url == "https://github.com/user/app-two/pull/1"

    # Verify atomic write mechanism actually preserves file contents
    with open(temp_repo_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 2
    data1 = json.loads(lines[0])
    data2 = json.loads(lines[1])
    assert data1["idea"]["title"] == "App One"
    assert data2["idea"]["title"] == "App Two"
