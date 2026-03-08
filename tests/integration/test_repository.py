import json
from collections.abc import Generator
from pathlib import Path

import pytest
from pydantic import BaseModel

from src.services.repository import JsonProjectRepository
from src.utils.errors import RepositoryError


class DummyModel(BaseModel):
    id: str
    name: str
    count: int


@pytest.fixture
def temp_repo_dir(tmp_path: Path) -> Generator[str, None, None]:
    """Yields a temporary directory for the repository."""
    repo_dir = tmp_path / "repo"
    yield str(repo_dir)


@pytest.fixture
def repository(temp_repo_dir: str) -> JsonProjectRepository[DummyModel]:
    """Creates a repository instance for testing."""
    return JsonProjectRepository(
        directory=temp_repo_dir,
        model_class=DummyModel,
        id_getter=lambda item: item.id,
    )


def test_save_and_get(repository: JsonProjectRepository[DummyModel], temp_repo_dir: str) -> None:
    """Test saving and retrieving an item."""
    item = DummyModel(id="test-1", name="Test Item", count=42)

    # Save the item
    repository.save(item)

    # Verify file was created
    file_path = Path(temp_repo_dir) / "test-1.json"
    assert file_path.exists()

    # Verify contents
    with open(file_path, "r") as f:
        data = json.load(f)
    assert data["id"] == "test-1"
    assert data["name"] == "Test Item"
    assert data["count"] == 42

    # Get the item back
    retrieved_item = repository.get("test-1")
    assert retrieved_item is not None
    assert retrieved_item.id == "test-1"
    assert retrieved_item.name == "Test Item"
    assert retrieved_item.count == 42


def test_get_not_found(repository: JsonProjectRepository[DummyModel]) -> None:
    """Test retrieving a non-existent item returns None."""
    assert repository.get("non-existent") is None


def test_get_all(repository: JsonProjectRepository[DummyModel]) -> None:
    """Test retrieving all items."""
    # Start with empty repo
    assert repository.get_all() == []

    # Save a few items
    item1 = DummyModel(id="test-1", name="Item 1", count=10)
    item2 = DummyModel(id="test-2", name="Item 2", count=20)
    repository.save(item1)
    repository.save(item2)

    # Get all items
    items = repository.get_all()
    assert len(items) == 2

    # Verify IDs (order is not guaranteed)
    ids = {item.id for item in items}
    assert ids == {"test-1", "test-2"}


from pytest_mock import MockerFixture


def test_save_invalid_dir(mocker: MockerFixture) -> None:
    """Test that initialization fails with an invalid directory."""
    mocker.patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied"))
    with pytest.raises(RepositoryError, match="Permission denied"):
        JsonProjectRepository(
            directory="/some/invalid/dir",
            model_class=DummyModel,
            id_getter=lambda item: item.id,
        )


def test_save_error(repository: JsonProjectRepository[DummyModel], mocker: MockerFixture) -> None:
    item = DummyModel(id="test-1", name="Item 1", count=10)
    mocker.patch("os.replace", side_effect=OSError("Permission denied"))

    with pytest.raises(RepositoryError, match="Permission denied"):
        repository.save(item)
