"""Tests for GitHub token scope validation."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.services.github import GitHubClient
from src.utils.errors import ConfigurationError, GitHubApiError


@pytest.fixture
def github_client(monkeypatch: pytest.MonkeyPatch) -> GitHubClient:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    return GitHubClient()


def test_validate_token_scope_success(github_client: Any) -> None:
    """Happy path: token has 'repo' scope."""
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {"X-OAuth-Scopes": "repo, user"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        github_client.validate_token_scope()
        mock_get.assert_called_once()


def test_validate_token_scope_missing_repo_scope(github_client: Any) -> None:
    """Error state: token is missing 'repo' scope."""
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {"X-OAuth-Scopes": "user, read:org"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(ConfigurationError, match="missing required 'repo' scope"):
            github_client.validate_token_scope()


def test_validate_token_scope_no_scopes_header(github_client: Any) -> None:
    """Error state: token has no scopes header."""
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(ConfigurationError, match="missing required 'repo' scope"):
            github_client.validate_token_scope()


def test_validate_token_scope_http_401(github_client: Any) -> None:
    """Error state: HTTP 401 returns a specific ConfigurationError."""
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 401

        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_get.side_effect = http_error

        with pytest.raises(ConfigurationError, match="invalid or expired"):
            github_client.validate_token_scope()


def test_validate_token_scope_http_error_other(github_client: Any) -> None:
    """Error state: Other HTTP errors raise GitHubApiError."""
    with patch("src.services.github.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}

        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_get.side_effect = http_error

        with pytest.raises(GitHubApiError, match="GitHub API Error"):
            github_client.validate_token_scope()


def test_validate_token_scope_network_error(github_client: Any) -> None:
    """Error state: Network errors raise GitHubApiError."""
    with patch("src.services.github.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection Failed")

        with pytest.raises(GitHubApiError, match="Network error"):
            github_client.validate_token_scope()
