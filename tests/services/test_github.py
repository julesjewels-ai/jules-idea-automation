"""Tests for GitHubClient."""

from typing import Any
from unittest.mock import patch

import pytest
import requests

from src.services.github import GitHubClient
from src.utils.errors import ConfigurationError, GitHubApiError
from tests.conftest import make_http_error, make_ok_response


@pytest.fixture
def github_client(monkeypatch: pytest.MonkeyPatch) -> GitHubClient:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = make_ok_response({})
        mock_response.headers = {"x-oauth-scopes": "repo, workflow"}
        mock_get.return_value = mock_response
        return GitHubClient()


# --- Init Validation ---


def test_init_validates_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = make_ok_response({})
        mock_response.headers = {"x-oauth-scopes": "repo, read:org"}
        mock_get.return_value = mock_response

        client = GitHubClient()
        assert client is not None
        mock_get.assert_called_once()


def test_init_raises_configuration_error_on_missing_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = make_ok_response({})
        mock_response.headers = {"x-oauth-scopes": "read:org"}
        mock_get.return_value = mock_response

        with pytest.raises(ConfigurationError, match="missing the 'repo' scope"):
            GitHubClient()


def test_init_raises_configuration_error_on_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = requests.Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with pytest.raises(ConfigurationError, match="invalid or expired"):
            GitHubClient()


def test_init_raises_configuration_error_on_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    with patch("src.services.github.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network down")

        with pytest.raises(ConfigurationError, match="Failed to validate GITHUB_TOKEN"):
            GitHubClient()


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

    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.request.side_effect = [
            # 1. GET latest commit SHA
            make_ok_response({"object": {"sha": latest_commit_sha}}),
            # 2. GET tree SHA
            make_ok_response({"tree": {"sha": base_tree_sha}}),
            # 3. POST blob 1
            make_ok_response({"sha": blob_sha_1}, 201),
            # 4. POST blob 2
            make_ok_response({"sha": blob_sha_2}, 201),
            # 5. POST new tree
            make_ok_response({"sha": new_tree_sha}, 201),
            # 6. POST new commit
            make_ok_response({"sha": new_commit_sha}, 201),
            # 7. PATCH ref update
            make_ok_response({}, 200),
        ]

        result = github_client.create_files(owner, repo, files, message, branch)

        assert result == {"commit_sha": new_commit_sha, "files_created": 2}
        assert mock_requests.request.call_count == 7


# --- Error Handling ---


def test_request_http_401_raises_github_api_error(github_client: Any) -> None:
    """401 errors should suggest token is invalid."""
    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.request.side_effect = make_http_error(401)
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError, match="GitHub API Error") as exc_info:
            github_client.get_user()

        assert "invalid or expired" in (exc_info.value.tip or "")


def test_request_http_403_raises_github_api_error(github_client: Any) -> None:
    """403 errors should suggest missing permissions."""
    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.request.side_effect = make_http_error(403)
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError) as exc_info:
            github_client.get_user()

        assert "permission" in (exc_info.value.tip or "").lower()


def test_request_http_404_raises_github_api_error(github_client: Any) -> None:
    """404 errors should suggest checking resource name."""
    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.request.side_effect = make_http_error(404)
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError) as exc_info:
            github_client.get_user()

        assert "not found" in (exc_info.value.tip or "").lower()


def test_request_http_422_with_message(github_client: Any) -> None:
    """422 errors should extract GitHub's error message when available."""
    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.request.side_effect = make_http_error(422, {"message": "Repository already exists"})
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError) as exc_info:
            github_client.create_repo("test", "test desc")

        assert "Repository already exists" in (exc_info.value.tip or "")


def test_request_timeout_raises_github_api_error(github_client: Any) -> None:
    """Timeout errors should surface as GitHubApiError."""
    with patch("src.services.http_client.requests") as mock_requests:
        mock_requests.request.side_effect = requests.exceptions.Timeout()
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError, match="timed out"):
            github_client.get_user()


def test_request_network_error_raises_github_api_error(github_client: Any) -> None:
    """ConnectionError should be retried and then surface as GitHubApiError."""
    with (
        patch("src.services.http_client.requests") as mock_requests,
        patch("src.services.http_client.time.sleep", return_value=None),
    ):
        mock_requests.request.side_effect = requests.exceptions.ConnectionError("DNS resolution failed")
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(GitHubApiError, match="connection failed after 3 attempts"):
            github_client.get_user()
