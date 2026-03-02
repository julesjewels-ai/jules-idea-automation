"""Tests for GitHubClient."""

from typing import Any
import pytest
from pytest import MonkeyPatch
from unittest.mock import patch, MagicMock
from src.services.github import GitHubClient


@pytest.fixture
def github_client(monkeypatch: MonkeyPatch) -> GitHubClient:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    return GitHubClient()


def test_create_files_success(github_client: GitHubClient) -> None:
    owner = "test-owner"
    repo = "test-repo"
    branch = "main"
    files = [
        {"path": "file1.txt", "content": "content1"},
        {"path": "dir/file2.txt", "content": "content2"}
    ]
    message = "feat: add files"

    # Mock data
    latest_commit_sha = "sha-latest-commit"
    base_tree_sha = "sha-base-tree"
    blob_sha_1 = "sha-blob-1"
    blob_sha_2 = "sha-blob-2"
    new_tree_sha = "sha-new-tree"
    new_commit_sha = "sha-new-commit"

    with patch("src.services.github.requests") as mock_requests:
        # Build a response factory
        def make_response(json_data: Any, status_code: int = 200) -> MagicMock:
            resp = MagicMock()
            resp.json.return_value = json_data
            resp.status_code = status_code
            resp.raise_for_status.return_value = None
            return resp

        # Configure responses in order of calls
        mock_requests.get.side_effect = [
            # 1. Get latest commit SHA
            make_response({"object": {"sha": latest_commit_sha}}),
            # 2. Get tree SHA
            make_response({"tree": {"sha": base_tree_sha}}),
        ]

        mock_requests.post.side_effect = [
            # 3. Create blob 1
            make_response({"sha": blob_sha_1}, 201),
            # 4. Create blob 2
            make_response({"sha": blob_sha_2}, 201),
            # 5. Create new tree
            make_response({"sha": new_tree_sha}, 201),
            # 6. Create new commit
            make_response({"sha": new_commit_sha}, 201),
        ]

        mock_requests.patch.return_value = make_response({}, 200)

        # Execute
        result = github_client.create_files(owner, repo, files, message, branch)

        # Verify result
        assert result == {
            "commit_sha": new_commit_sha,
            "files_created": 2
        }

        # Verify blob creation calls
        blob_calls = mock_requests.post.call_args_list
        assert blob_calls[0].kwargs["json"] == {"content": "content1", "encoding": "utf-8"}
        assert blob_calls[1].kwargs["json"] == {"content": "content2", "encoding": "utf-8"}

        # Verify ref update
        mock_requests.patch.assert_called_once()
        patch_call = mock_requests.patch.call_args
        assert patch_call.kwargs["json"] == {"sha": new_commit_sha}
