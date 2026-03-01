"""Integration tests for JsonProjectRepository."""

from pathlib import Path

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository


def test_json_project_repository_save_and_get(tmp_path: Path) -> None:
    """Test saving and retrieving an item from JsonProjectRepository."""
    # Setup
    repo_file = tmp_path / "test_repo.jsonl"
    repository = JsonProjectRepository(str(repo_file), WorkflowResult)

    # Create dummy data
    idea = IdeaResponse(
        title="Test Idea",
        description="A great test idea.",
        slug="test-idea",
        tech_stack=["python", "pytest"],
        features=["feature 1"]
    )
    result = WorkflowResult(
        idea=idea,
        repo_url="https://github.com/test/test-idea",
        session_id="session-123",
        session_url="https://jules.google.com/sessions/123"
    )

    # Save
    repository.save(result)

    # Verify file content
    assert repo_file.exists()
    content = repo_file.read_text(encoding="utf-8")
    assert "test-idea" in content

    # Reload and Get
    retrieved = repository.get("test-idea")
    assert retrieved is not None
    assert retrieved.repo_url == "https://github.com/test/test-idea"
    assert retrieved.idea.slug == "test-idea"

    # Save another to check appending and updating
    idea2 = IdeaResponse(
        title="Test Idea 2",
        description="Another idea.",
        slug="test-idea-2",
        tech_stack=["python"],
        features=[]
    )
    result2 = WorkflowResult(
        idea=idea2,
        repo_url="https://github.com/test/test-idea-2",
        session_id=None,
        session_url=None
    )

    repository.save(result2)

    # Update first one
    result.session_id = "session-456"
    repository.save(result)

    # List all
    all_items = repository.list_all()
    assert len(all_items) == 2

    updated_result = repository.get("test-idea")
    assert updated_result is not None
    assert updated_result.session_id == "session-456"
