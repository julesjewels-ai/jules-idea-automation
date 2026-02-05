from src.core.models import ProjectFile
import pytest
from pydantic import ValidationError

def test_project_file_path_traversal():
    """Test that ProjectFile rejects path traversal attempts."""
    unsafe_paths = [
        "../../etc/passwd",
        "/etc/passwd",
        "src/../../secrets.env",
        "../parent.py"
    ]

    for path in unsafe_paths:
        # Match just "Path must be relative" as it covers both error cases
        with pytest.raises(ValidationError, match="Path must be relative"):
            ProjectFile(path=path, content="unsafe", description="unsafe")

def test_project_file_safe_path():
    """Test that ProjectFile accepts safe paths."""
    safe_paths = [
        "src/main.py",
        "README.md",
        "tests/test_app.py",
        ".env.example"
    ]

    for path in safe_paths:
        ProjectFile(path=path, content="safe", description="safe")
