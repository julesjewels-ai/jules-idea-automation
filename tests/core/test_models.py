import pytest
from pydantic import ValidationError
from src.core.models import ProjectFile

def test_project_file_valid_path():
    """Test that valid paths are accepted."""
    pf = ProjectFile(path="src/main.py", content="print('hello')", description="Main file")
    assert pf.path == "src/main.py"

    pf = ProjectFile(path="tests/test_core.py", content="", description="")
    assert pf.path == "tests/test_core.py"

def test_project_file_path_traversal():
    """Test that path traversal attempts raise ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        ProjectFile(path="../../etc/passwd", content="", description="")
    # We expect some error message related to path safety
    # The exact message depends on implementation, but checking for "path" is safe for now
    # or I can assert on the specific error later once implemented
    pass

def test_project_file_absolute_path():
    """Test that absolute paths raise ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        ProjectFile(path="/etc/passwd", content="", description="")
    pass

def test_project_file_restricted_dir():
    """Test that restricted directories are blocked."""
    with pytest.raises(ValidationError) as excinfo:
        ProjectFile(path=".git/config", content="", description="")
    pass
