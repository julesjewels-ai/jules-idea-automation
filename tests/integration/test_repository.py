"""Integration tests for JsonProjectRepository."""

import json
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository
from src.utils.errors import RepositoryError


@pytest.fixture
def temp_repo_file() -> Generator[str, None, None]:
    """Yield a temporary file path for the repository."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def sample_result() -> WorkflowResult:
    """Provide a valid sample WorkflowResult."""
    return WorkflowResult(
        idea=IdeaResponse(
            title="Test App",
            description="A test app",
            slug="test-app",
            tech_stack=["python", "pytest"],
            features=["testing"],
        ),
        repo_url="https://github.com/user/test-app",
        session_id="session_123",
        session_url="https://jules.google.com/sessions/session_123",
    )


def test_json_project_repository_save_and_get(temp_repo_file: str, sample_result: WorkflowResult) -> None:
    """Test saving an item securely using atomic writes, then retrieving it."""
    repo = JsonProjectRepository(
        file_path=temp_repo_file,
        model_class=WorkflowResult,
        id_getter=lambda result: result.idea.slug,
    )

    # File starts empty
    assert repo.get("test-app") is None
    assert len(repo.get_all()) == 0

    # Save the result
    repo.save(sample_result)

    # Verify atomic write by checking standard file loading outside repo
    data = json.loads(Path(temp_repo_file).read_text(encoding="utf-8"))
    assert "test-app" in data
    assert data["test-app"]["repo_url"] == "https://github.com/user/test-app"

    # Verify retrieval
    retrieved = repo.get("test-app")
    assert retrieved is not None
    assert retrieved.idea.slug == "test-app"
    assert retrieved.session_id == "session_123"

    # Verify get_all
    all_results = repo.get_all()
    assert len(all_results) == 1
    assert all_results[0].idea.title == "Test App"


def test_json_project_repository_save_write_failure(temp_repo_file: str, sample_result: WorkflowResult) -> None:
    """Test that a RepositoryError is raised on write failure (e.g. invalid permissions)."""
    # Create a read-only directory to force a write error
    dir_path = Path(temp_repo_file).parent / "read_only_dir"
    dir_path.mkdir(exist_ok=True)
    os.chmod(dir_path, 0o400)  # Read-only

    invalid_file = dir_path / "repo.json"

    repo = JsonProjectRepository(
        file_path=str(invalid_file),
        model_class=WorkflowResult,
        id_getter=lambda result: result.idea.slug,
    )

    with pytest.raises(RepositoryError, match="Failed to save item to repository"):
        repo.save(sample_result)

    # Cleanup
    os.chmod(dir_path, 0o700)
    try:
        dir_path.rmdir()
    except OSError:
        pass
