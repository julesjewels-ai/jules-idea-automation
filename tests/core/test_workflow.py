import pytest
from unittest.mock import Mock, patch
from src.core.workflow import IdeaWorkflow

class TestIdeaWorkflow:
    @pytest.fixture
    def mock_github(self):
        return Mock()

    @pytest.fixture
    def mock_gemini(self):
        return Mock()

    @pytest.fixture
    def mock_jules(self):
        return Mock()

    @pytest.fixture
    def workflow(self, mock_github, mock_gemini, mock_jules):
        return IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

    def test_generate_scaffold_creates_files(self, workflow, mock_gemini, mock_github):
        # Arrange
        idea_data = {
            "title": "Test Project",
            "description": "A test project",
            "slug": "test-project",
            "tech_stack": ["python"],
            "features": ["feature1"]
        }

        mock_gemini.generate_project_scaffold.return_value = {
            "files": [
                {"path": "main.py", "content": "print('hello')"},
                {"path": "README.md", "content": "should be ignored"}
            ],
            "requirements": ["pytest"],
            "run_command": "python main.py"
        }

        mock_github.create_files.return_value = {"files_created": 2}

        # Act
        workflow._generate_scaffold("testuser", idea_data, verbose=False)

        # Assert
        # Check that create_file was called for README (separate call)
        mock_github.create_file.assert_called_once()
        args, kwargs = mock_github.create_file.call_args
        assert kwargs['path'] == "README.md"

        # Check that create_files was called with correct files
        mock_github.create_files.assert_called_once()
        args, kwargs = mock_github.create_files.call_args
        files_arg = kwargs['files']

        # Should contain main.py and requirements.txt
        paths = [f['path'] for f in files_arg]
        assert "main.py" in paths
        assert "requirements.txt" in paths
        assert "README.md" not in paths # Should be filtered out from batch commit

        # specific content check
        req_file = next(f for f in files_arg if f['path'] == 'requirements.txt')
        assert req_file['content'] == "pytest"

    def test_generate_scaffold_no_files(self, workflow, mock_gemini, mock_github):
        # Arrange
        idea_data = {
            "title": "Test Project",
            "description": "A test project",
            "slug": "test-project"
        }

        mock_gemini.generate_project_scaffold.return_value = {
            "files": [],
            "requirements": []
        }

        # Act
        workflow._generate_scaffold("testuser", idea_data, verbose=False)

        # Assert
        mock_github.create_file.assert_called_once() # README still created
        mock_github.create_files.assert_not_called() # No other files
