
import pytest
import os
from unittest.mock import MagicMock, patch
from src.services.github import GitHubClient

# Mock environment variable
@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}):
        yield

@pytest.fixture
def github_client(mock_env):
    with patch("requests.Session") as mock_session:
        client = GitHubClient()
        # Mock the session object
        client.session = MagicMock()
        client.session.headers = {}
        yield client

def test_github_client_init_error():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable is not set"):
            GitHubClient()

def test_get_user(github_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"login": "testuser"}
    github_client.session.get.return_value = mock_response

    user = github_client.get_user()

    assert user == {"login": "testuser"}
    github_client.session.get.assert_called_once()
    assert github_client.session.get.call_args[0][0].endswith("/user")

def test_create_repo(github_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"name": "test-repo"}
    github_client.session.post.return_value = mock_response

    repo = github_client.create_repo("test-repo", "description")

    assert repo == {"name": "test-repo"}
    github_client.session.post.assert_called_once()
    assert github_client.session.post.call_args[0][0].endswith("/user/repos")
    assert github_client.session.post.call_args[1]["json"]["name"] == "test-repo"

def test_create_file(github_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": {}}
    github_client.session.put.return_value = mock_response

    result = github_client.create_file("owner", "repo", "path/file.txt", "content", "msg")

    assert result == {"content": {}}
    github_client.session.put.assert_called_once()
    assert "repos/owner/repo/contents/path/file.txt" in github_client.session.put.call_args[0][0]

def test_create_files(github_client):
    # Setup mocks for the sequence of calls

    # 1. Get Ref
    mock_ref_resp = MagicMock()
    mock_ref_resp.json.return_value = {"object": {"sha": "latest-sha"}}

    # 2. Get Commit
    mock_commit_resp = MagicMock()
    mock_commit_resp.json.return_value = {"tree": {"sha": "base-tree-sha"}}

    # 3. Create Blobs (called once per file)
    mock_blob_resp = MagicMock()
    mock_blob_resp.json.return_value = {"sha": "blob-sha"}

    # 4. Create Tree
    mock_tree_resp = MagicMock()
    mock_tree_resp.json.return_value = {"sha": "new-tree-sha"}

    # 5. Create Commit
    mock_new_commit_resp = MagicMock()
    mock_new_commit_resp.json.return_value = {"sha": "new-commit-sha"}

    # 6. Update Ref
    mock_update_ref_resp = MagicMock()

    # Configure side effects for get/post/patch
    github_client.session.get.side_effect = [mock_ref_resp, mock_commit_resp]
    github_client.session.post.side_effect = [mock_blob_resp, mock_tree_resp, mock_new_commit_resp]
    github_client.session.patch.return_value = mock_update_ref_resp

    files = [{"path": "file1.txt", "content": "foo"}]

    result = github_client.create_files("owner", "repo", files, "message")

    assert result["commit_sha"] == "new-commit-sha"
    assert result["files_created"] == 1

    # Verify sequence roughly
    assert github_client.session.get.call_count == 2
    assert github_client.session.post.call_count == 3
    assert github_client.session.patch.call_count == 1
