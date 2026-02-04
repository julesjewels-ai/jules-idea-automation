import pytest
import requests
from src.services.github import GitHubClient

@pytest.fixture
def github_client(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    return GitHubClient()

def test_create_files_success(github_client, requests_mock):
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

    # 1. Get latest commit SHA
    requests_mock.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}",
        json={"object": {"sha": latest_commit_sha}}
    )

    # 2. Get tree SHA
    requests_mock.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/commits/{latest_commit_sha}",
        json={"tree": {"sha": base_tree_sha}}
    )

    # 3. Create blobs (called twice)
    # We can match on content if we want strictness, or just return based on order/url
    requests_mock.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/blobs",
        [
            {"json": {"sha": blob_sha_1}, "status_code": 201},
            {"json": {"sha": blob_sha_2}, "status_code": 201}
        ]
    )

    # 4. Create new tree
    requests_mock.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees",
        json={"sha": new_tree_sha},
        status_code=201
    )

    # 5. Create new commit
    requests_mock.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/commits",
        json={"sha": new_commit_sha},
        status_code=201
    )

    # 6. Update ref
    requests_mock.patch(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}",
        json={},
        status_code=200
    )

    # Execute
    result = github_client.create_files(owner, repo, files, message, branch)

    # Verify result
    assert result == {
        "commit_sha": new_commit_sha,
        "files_created": 2
    }

    # Verify specific request payloads if necessary
    # Example: Check that update ref was called with correct SHA
    history = requests_mock.request_history
    assert history[-1].method == "PATCH"
    assert history[-1].url == f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    assert history[-1].json() == {"sha": new_commit_sha}

    # Verify blob creation payloads
    blob_requests = [r for r in history if r.url.endswith("/git/blobs") and r.method == "POST"]
    assert len(blob_requests) == 2
    assert blob_requests[0].json() == {"content": "content1", "encoding": "utf-8"}
    assert blob_requests[1].json() == {"content": "content2", "encoding": "utf-8"}
