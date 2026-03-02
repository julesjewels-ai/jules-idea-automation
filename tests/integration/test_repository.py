import tempfile
from pathlib import Path

from pydantic import BaseModel

from src.services.repository import JsonProjectRepository
from src.core.interfaces import ProjectRepository

class DummyModel(BaseModel):
    id: int
    name: str

def test_repository_interface_and_persistence() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_file = Path(temp_dir) / "test_repo.json"

        # Test Interface
        repo: ProjectRepository[DummyModel] = JsonProjectRepository(str(repo_file), DummyModel)

        item1 = DummyModel(id=1, name="Item 1")
        item2 = DummyModel(id=2, name="Item 2")

        # Save items
        repo.save(item1)
        repo.save(item2)

        # Verify persistence and retrieval
        items = repo.get_all()
        assert len(items) == 2
        assert items[0].id == 1
        assert items[0].name == "Item 1"
        assert items[1].id == 2
        assert items[1].name == "Item 2"

        # Verify file structure
        assert repo_file.exists()
        content = repo_file.read_text(encoding="utf-8")
        assert "Item 1" in content
        assert "Item 2" in content
