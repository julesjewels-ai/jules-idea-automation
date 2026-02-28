"""Integration test for JsonProjectRepository."""

import json
from pathlib import Path
import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository


@pytest.fixture
def temp_repo_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory for repository data."""
    repo_dir = tmp_path / "projects"
    return repo_dir


@pytest.fixture
def sample_result() -> WorkflowResult:
    """Fixture providing a sample WorkflowResult."""
    idea = IdeaResponse(
        title="Test Idea",
        description="A test description",
        slug="test-idea",
        tech_stack=["Python"],
        features=["Test Feature"]
    )
    return WorkflowResult(
        idea=idea,
        repo_url="https://github.com/user/test-idea",
        session_id="12345",
        session_url="https://jules.googleapis.com/v1alpha/sessions/12345",
        pr_url="https://github.com/user/test-idea/pull/1"
    )


def test_json_project_repository_lifecycle(temp_repo_dir: Path, sample_result: WorkflowResult) -> None:
    """Test the complete lifecycle of saving and retrieving a project."""

    # 1. Initialize the repository
    repo = JsonProjectRepository(data_dir=str(temp_repo_dir))

    # 2. Verify the directory was created
    assert temp_repo_dir.exists()
    assert temp_repo_dir.is_dir()

    # 3. Verify it's initially empty
    assert len(repo.list_all()) == 0
    assert repo.get_by_slug("test-idea") is None

    # 4. Save the result
    repo.save(sample_result)

    # 5. Verify the file was created
    file_path = temp_repo_dir / "test-idea.json"
    assert file_path.exists()
    assert file_path.is_file()

    # Verify file content is valid JSON and matches expectations
    content = json.loads(file_path.read_text(encoding="utf-8"))
    assert content["idea"]["slug"] == "test-idea"
    assert content["repo_url"] == "https://github.com/user/test-idea"

    # 6. Retrieve the result by slug
    retrieved_result = repo.get_by_slug("test-idea")

    # Verify the retrieved object is identical to the saved one
    assert retrieved_result is not None
    assert isinstance(retrieved_result, WorkflowResult)
    assert retrieved_result.idea.title == "Test Idea"
    assert retrieved_result.idea.slug == "test-idea"
    assert retrieved_result.repo_url == "https://github.com/user/test-idea"
    assert retrieved_result.session_id == "12345"
    assert retrieved_result.pr_url == "https://github.com/user/test-idea/pull/1"

    # 7. List all results
    all_results = repo.list_all()
    assert len(all_results) == 1
    assert all_results[0].idea.slug == "test-idea"

    # 8. Save a second result
    idea2 = IdeaResponse(
        title="Another Idea",
        description="Another test description",
        slug="another-idea"
    )
    result2 = WorkflowResult(
        idea=idea2,
        repo_url="https://github.com/user/another-idea"
    )

    repo.save(result2)

    # Verify list_all returns both
    all_results = repo.list_all()
    assert len(all_results) == 2
    slugs = [r.idea.slug for r in all_results]
    assert "test-idea" in slugs
    assert "another-idea" in slugs
