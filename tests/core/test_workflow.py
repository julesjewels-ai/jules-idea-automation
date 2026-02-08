import pytest
from unittest.mock import Mock, call
from src.core.workflow import IdeaWorkflow
from src.core.models import IdeaResponse, ProjectScaffold

@pytest.fixture
def mock_github():
    return Mock()

@pytest.fixture
def mock_gemini():
    return Mock()

@pytest.fixture
def mock_jules():
    return Mock()

@pytest.fixture
def workflow(mock_github, mock_gemini, mock_jules):
    return IdeaWorkflow(github=mock_github, gemini=mock_gemini, jules=mock_jules)

@pytest.fixture
def sample_idea_data():
    return {
        "title": "My Awesome Idea",
        "description": "A very detailed description of the idea.",
        "slug": "my-awesome-idea",
        "tech_stack": ["python", "pytest"],
        "features": ["feature1", "feature2"]
    }

@pytest.fixture
def sample_scaffold():
    return {
        "files": [
            {"path": "main.py", "content": "print('hello')", "description": "Main file"},
            {"path": "README.md", "content": "# Readme", "description": "Readme file"}
        ],
        "requirements": ["requests", "pytest"],
        "run_command": "python main.py"
    }

def test_workflow_initialization(mocker):
    """Test that default clients are created if not provided."""
    mock_github_cls = mocker.patch("src.core.workflow.GitHubClient")
    mock_gemini_cls = mocker.patch("src.core.workflow.GeminiClient")
    mock_jules_cls = mocker.patch("src.core.workflow.JulesClient")

    wf = IdeaWorkflow()

    assert wf.github == mock_github_cls.return_value
    assert wf.gemini == mock_gemini_cls.return_value
    assert wf.jules == mock_jules_cls.return_value

def test_execute_happy_path(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data, sample_scaffold
):
    """Test the happy path of execute."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_repo.return_value = None
    mock_github.create_files.return_value = {"files_created": 2}

    mock_gemini.generate_project_scaffold.return_value = sample_scaffold

    mock_poll_until = mocker.patch("src.core.workflow.poll_until", return_value=True)
    mocker.patch("src.core.workflow.build_readme", return_value="# Mock Readme")
    mocker.patch("src.core.workflow.print_workflow_report")

    mock_jules.source_exists.return_value = True
    mock_jules.create_session.return_value = {"id": "session-123", "url": "http://jules/session/123"}

    # Act
    result = workflow.execute(sample_idea_data, verbose=False)

    # Assert
    # 1. Create Repository
    mock_github.get_user.assert_called_once()
    mock_github.create_repo.assert_called_once_with(
        name="my-awesome-idea",
        description="A very detailed description of the idea.",
        private=False
    )

    # 2. Generate Scaffold
    mock_gemini.generate_project_scaffold.assert_called_once_with(sample_idea_data)

    # 3. Create Files (README + Scaffold)
    # Verify README creation
    mock_github.create_file.assert_called_once()
    args, kwargs = mock_github.create_file.call_args
    assert kwargs['path'] == "README.md"
    assert kwargs['content'] == "# Mock Readme"

    # Verify Scaffold creation (excluding README, including requirements)
    mock_github.create_files.assert_called_once()
    files_arg = mock_github.create_files.call_args[1]['files']

    # Expecting main.py and requirements.txt (README.md filtered out)
    assert len(files_arg) == 2
    assert any(f['path'] == 'main.py' for f in files_arg)
    assert any(f['path'] == 'requirements.txt' for f in files_arg)
    assert not any(f['path'] == 'README.md' for f in files_arg)

    # 4. Create Session
    mock_poll_until.assert_called_once()
    mock_jules.create_session.assert_called_once()

    assert result.repo_url == "https://github.com/testuser/my-awesome-idea"
    assert result.session_id == "session-123"

def test_execute_scaffold_filtering(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data, sample_scaffold
):
    """Test that scaffold files are correctly prepared/filtered."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": 2}
    mock_gemini.generate_project_scaffold.return_value = sample_scaffold

    # Mock Jules session creation to return a dict (to satisfy WorkflowResult validation)
    mock_jules.create_session.return_value = {"id": "sess-1", "url": "url-1"}
    mock_jules.source_exists.return_value = True

    mocker.patch("src.core.workflow.poll_until", return_value=True)
    mocker.patch("src.core.workflow.build_readme", return_value="# Mock Readme")
    mocker.patch("src.core.workflow.print_workflow_report")

    # Act
    workflow.execute(sample_idea_data, verbose=False)

    # Assert
    mock_github.create_files.assert_called_once()
    files_created = mock_github.create_files.call_args[1]['files']

    # Check that README.md from scaffold is NOT present
    assert not any(f['path'] == 'README.md' for f in files_created)
    # Check that requirements.txt IS present
    assert any(f['path'] == 'requirements.txt' for f in files_created)
    # Check content of requirements.txt
    req_file = next(f for f in files_created if f['path'] == 'requirements.txt')
    assert "requests" in req_file['content']
    assert "pytest" in req_file['content']

@pytest.mark.parametrize("scaffold_files, requirements, expected_files_count, expected_paths", [
    # Case 1: Empty files, no requirements
    ([], [], 0, []),
    # Case 2: Only non-README files, no requirements
    ([{"path": "test.py", "content": "print('hi')"}], [], 1, ["test.py"]),
    # Case 3: README only (should be filtered), no requirements
    ([{"path": "README.md", "content": "# Readme"}], [], 0, []),
    # Case 4: Non-README + requirements
    ([{"path": "test.py", "content": "hi"}], ["req1"], 2, ["test.py", "requirements.txt"]),
])
def test_execute_scaffold_variations(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data,
    scaffold_files, requirements, expected_files_count, expected_paths
):
    """Parametrized test for scaffold file handling logic via execute."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": expected_files_count}

    # Mock Jules
    mock_jules.create_session.return_value = {"id": "sess-1", "url": "url-1"}
    mock_jules.source_exists.return_value = True

    scaffold = {
        "files": scaffold_files,
        "requirements": requirements,
        "run_command": "echo 'run'"
    }
    mock_gemini.generate_project_scaffold.return_value = scaffold

    mocker.patch("src.core.workflow.poll_until", return_value=True)
    mocker.patch("src.core.workflow.build_readme", return_value="# Mock Readme")
    mocker.patch("src.core.workflow.print_workflow_report")

    # Act
    workflow.execute(sample_idea_data, verbose=False)

    # Assert
    if expected_files_count > 0:
        mock_github.create_files.assert_called_once()
        files_created = mock_github.create_files.call_args[1]['files']
        assert len(files_created) == expected_files_count
        created_paths = [f['path'] for f in files_created]
        assert sorted(created_paths) == sorted(expected_paths)
    else:
        mock_github.create_files.assert_not_called()

def test_execute_timeout(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data, sample_scaffold
):
    """Test behavior when polling times out."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_gemini.generate_project_scaffold.return_value = sample_scaffold
    mocker.patch("src.core.workflow.poll_until", return_value=False)
    mocker.patch("src.core.workflow.build_readme", return_value="# Mock Readme")
    mocker.patch("src.core.workflow.print_workflow_report")

    # Act
    result = workflow.execute(sample_idea_data, verbose=False)

    # Assert
    mock_jules.create_session.assert_not_called()
    assert result.session_id is None
    assert result.repo_url == "https://github.com/testuser/my-awesome-idea"

def test_execute_timeout_verbose(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data, sample_scaffold, capsys
):
    """Test behavior when polling times out with verbose logging."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": 2}
    mock_gemini.generate_project_scaffold.return_value = sample_scaffold
    mocker.patch("src.core.workflow.poll_until", return_value=False)
    mocker.patch("src.core.workflow.build_readme")
    mocker.patch("src.core.workflow.print_workflow_report")

    # Act
    workflow.execute(sample_idea_data, verbose=True)

    # Assert
    captured = capsys.readouterr()
    assert "WARNING: Source" in captured.out
    assert "was not found in Jules" in captured.out

def test_execute_poll_callback(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data, sample_scaffold, capsys
):
    """Test that the poll callback prints status when verbose is True."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": 2}
    mock_gemini.generate_project_scaffold.return_value = sample_scaffold
    mock_jules.create_session.return_value = {"id": "sess-1", "url": "url-1"}
    mock_jules.source_exists.return_value = True

    # Custom side effect to call the on_poll callback
    def mock_poll_until(condition, timeout, interval, on_poll):
        on_poll(10) # Simulate 10 seconds elapsed
        return True

    mocker.patch("src.core.workflow.poll_until", side_effect=mock_poll_until)
    mocker.patch("src.core.workflow.build_readme")
    mocker.patch("src.core.workflow.print_workflow_report")

    # Act
    workflow.execute(sample_idea_data, verbose=True)

    # Assert
    captured = capsys.readouterr()
    assert "Source not yet indexed (10s elapsed)..." in captured.out

def test_execute_private_repo(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data, sample_scaffold
):
    """Test private repository creation."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": 2}
    mock_gemini.generate_project_scaffold.return_value = sample_scaffold

    # Mock Jules
    mock_jules.create_session.return_value = {"id": "sess-1", "url": "url-1"}

    mocker.patch("src.core.workflow.poll_until", return_value=True)
    mocker.patch("src.core.workflow.build_readme")
    mocker.patch("src.core.workflow.print_workflow_report")

    # Act
    workflow.execute(sample_idea_data, private=True, verbose=False)

    # Assert
    mock_github.create_repo.assert_called_with(
        name="my-awesome-idea",
        description=sample_idea_data["description"][:350],
        private=True
    )

def test_execute_verbose_logging(
    mocker, workflow, mock_github, mock_gemini, mock_jules, sample_idea_data, sample_scaffold, capsys
):
    """Test that verbose logging produces output."""
    # Arrange
    mock_github.get_user.return_value = {"login": "testuser"}
    mock_github.create_files.return_value = {"files_created": 2}
    mock_gemini.generate_project_scaffold.return_value = sample_scaffold

    # Mock Jules
    mock_jules.create_session.return_value = {"id": "sess-1", "url": "url-1"}

    mocker.patch("src.core.workflow.poll_until", return_value=True)
    mocker.patch("src.core.workflow.build_readme")

    # Act
    workflow.execute(sample_idea_data, verbose=True)

    # Assert
    captured = capsys.readouterr()
    assert "Processing Idea: My Awesome Idea" in captured.out
    assert "Creating public GitHub repository" in captured.out
    assert "Generating MVP scaffold" in captured.out
    assert "Source found! Creating session" in captured.out
