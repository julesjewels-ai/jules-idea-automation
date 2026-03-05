"""Tests for GitHubClient."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.services.github import GitHubClient
from src.utils.errors import GitHubApiError


@pytest.fixture
def github_client(monkeypatch: pytest.MonkeyPatch) -> GitHubClient:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    return GitHubClient()


def _make_response(json_data: Any, status_code: int = 200) -> MagicMock:
    """Factory for mock responses."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.text = "{}"
    resp.raise_for_status.return_value = None
    return resp


def _make_http_error(status_code: int, body: dict[str, Any] | None = None) -> requests.exceptions.HTTPError:
    """Factory for HTTPError with a mock response."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body or {}
    error = requests.exceptions.HTTPError(response=response)
    return error


# --- Happy Path ---


def test_create_files_success(github_client: Any) -> None:
    owner = "test-owner"
    repo = "test-repo"
    branch = "main"
    files = [{"path": "file1.txt", "content": "content1"}, {"path": "dir/file2.txt", "content": "content2"}]
    message = "feat: add files"

    latest_commit_sha = "sha-latest-commit"
    base_tree_sha = "sha-base-tree"
    blob_sha_1 = "sha-blob-1"
    blob_sha_2 = "sha-blob-2"
    new_tree_sha = "sha-new-tree"
    new_commit_sha = "sha-new-commit"

    with patch("src.services.github.requests") as mock_requests:
        mock_requests.request.side_effect = [
            # 1. GET latest commit SHA
            _make_response({"object": {"sha": latest_commit_sha}}),
            # 2. GET tree SHA
            _make_response({"tree": {"sha": base_tree_sha}}),
            # 3. POST blob 1
            _make_response({"sha": blob_sha_1}, 201),
            # 4. POST blob 2
            _make_response({"sha": blob_sha_2}, 201),
            # 5. POST new tree
            _make_response({"sha": new_tree_sha}, 201),
            # 6. POST new commit
            _make_response({"sha": new_commit_sha}, 201),
            # 7. PATCH ref update
            _make_response({}, 200),
        ]

        result = github_client.create_files(owner, repo, files, message, branch)

        assert result == {"commit_sha": new_commit_sha, "files_created": 2}
        assert mock_requests.request.call_count == 7


# --- Error Handling ---


def test_request_http_401_raises_github_api_error(github_client: Any) -> None:
    """401 errors should suggest token is invalid."""
    with patch("src.services.github.requests") as mock_requests:
        mock_requests.request.side_effect = _make_http_error(401)
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError, match="GitHub API Error") as exc_info:
            github_client.get_user()

        assert "invalid or expired" in (exc_info.value.tip or "")


def test_request_http_403_raises_github_api_error(github_client: Any) -> None:
    """403 errors should suggest missing permissions."""
    with patch("src.services.github.requests") as mock_requests:
        mock_requests.request.side_effect = _make_http_error(403)
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError) as exc_info:
            github_client.get_user()

        assert "permission" in (exc_info.value.tip or "").lower()


def test_request_http_404_raises_github_api_error(github_client: Any) -> None:
    """404 errors should suggest checking resource name."""
    with patch("src.services.github.requests") as mock_requests:
        mock_requests.request.side_effect = _make_http_error(404)
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError) as exc_info:
            github_client.get_user()

        assert "not found" in (exc_info.value.tip or "").lower()


def test_request_http_422_with_message(github_client: Any) -> None:
    """422 errors should extract GitHub's error message when available."""
    with patch("src.services.github.requests") as mock_requests:
        mock_requests.request.side_effect = _make_http_error(422, {"message": "Repository already exists"})
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError) as exc_info:
            github_client.create_repo("test", "test desc")

        assert "Repository already exists" in (exc_info.value.tip or "")


def test_request_timeout_raises_github_api_error(github_client: Any) -> None:
    """Timeout errors should surface as GitHubApiError."""
    with patch("src.services.github.requests") as mock_requests:
        mock_requests.request.side_effect = requests.exceptions.Timeout()
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError, match="timed out"):
            github_client.get_user()


def test_request_network_error_raises_github_api_error(github_client: Any) -> None:
    """Generic network errors should surface as GitHubApiError."""
    with patch("src.services.github.requests") as mock_requests:
        mock_requests.request.side_effect = requests.exceptions.ConnectionError("DNS resolution failed")
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError, match="Network error"):
            github_client.get_user()
