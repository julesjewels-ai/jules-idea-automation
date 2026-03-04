"""Integration tests for ProjectRepository implementation."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

import pytest

from src.core.models import IdeaResponse, WorkflowResult
from src.services.repository import JsonProjectRepository


@pytest.fixture
def temp_repo_file() -> Generator[str, None, None]:
    """Provide a temporary file path for repository testing."""
    fd, temp_path = tempfile.mkstemp(prefix="test_repo_", suffix=".jsonl")
    os.close(fd)
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_result() -> WorkflowResult:
    """Provide a sample WorkflowResult for testing."""
    idea = IdeaResponse(
        title="Test Idea",
        description="A great idea",
        slug="test-idea",
        tech_stack=["python", "pytest"],
        features=["auth", "db"]
    )
    return WorkflowResult(
        idea=idea,
        repo_url="https://github.com/user/test-idea",
        session_id="session_123",
        session_url="https://jules.app/session_123"
    )


def test_json_project_repository_integration(temp_repo_file: str, sample_result: WorkflowResult) -> None:
    """Test full cycle of save and retrieve with JsonProjectRepository."""
    repo = JsonProjectRepository(temp_repo_file, WorkflowResult)

    # Empty repository initially
    assert len(repo.get_all()) == 0

    # Save a record
    repo.save(sample_result)

    # Verify we can retrieve it
    results = repo.get_all()
    assert len(results) == 1

    retrieved = results[0]
    assert retrieved.repo_url == sample_result.repo_url
    assert retrieved.session_id == sample_result.session_id
    assert retrieved.idea.title == sample_result.idea.title

    # Save another record
    idea2 = IdeaResponse(
        title="Second Idea",
        description="Another idea",
        slug="second-idea"
    )
    result2 = WorkflowResult(
        idea=idea2,
        repo_url="https://github.com/user/second-idea"
    )

    repo.save(result2)

    # Verify multiple records
    results_after = repo.get_all()
    assert len(results_after) == 2
    assert results_after[0].idea.title == "Test Idea"
    assert results_after[1].idea.title == "Second Idea"
