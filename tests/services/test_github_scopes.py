from unittest.mock import MagicMock, patch

import pytest
import requests

from src.services.github import GitHubClient
from src.utils.errors import ConfigurationError


@pytest.fixture
def mock_github_client():
    return GitHubClient(token="fake-token")


@patch("requests.get")
def test_validate_token_scopes_success(mock_get, mock_github_client):
    """Test that validation passes when the token has the 'repo' scope."""
    mock_response = MagicMock()
    mock_response.headers = {"X-OAuth-Scopes": "repo, workflow, read:org"}
    mock_get.return_value = mock_response

    # Should not raise an exception
    mock_github_client.validate_token_scopes()

    mock_get.assert_called_once_with(
        "https://api.github.com/user",
        headers={
            "Authorization": "token fake-token",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=30,
    )


@patch("requests.get")
def test_validate_token_scopes_missing_repo_scope(mock_get, mock_github_client):
    """Test that validation fails when the token is missing the 'repo' scope."""
    mock_response = MagicMock()
    mock_response.headers = {"X-OAuth-Scopes": "read:org, user"}
    mock_get.return_value = mock_response

    with pytest.raises(ConfigurationError) as exc_info:
        mock_github_client.validate_token_scopes()

    assert "missing the required 'repo' scope" in str(exc_info.value)
    assert "read:org, user" in exc_info.value.tip


@patch("requests.get")
def test_validate_token_scopes_no_scopes_header(mock_get, mock_github_client):
    """Test that validation fails when the X-OAuth-Scopes header is absent."""
    mock_response = MagicMock()
    mock_response.headers = {}
    mock_get.return_value = mock_response

    with pytest.raises(ConfigurationError) as exc_info:
        mock_github_client.validate_token_scopes()

    assert "missing the required 'repo' scope" in str(exc_info.value)
    assert "none" in exc_info.value.tip


@patch("requests.get")
def test_validate_token_scopes_network_error(mock_get, mock_github_client):
    """Test that validation handles network errors properly."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

    with pytest.raises(ConfigurationError) as exc_info:
        mock_github_client.validate_token_scopes()

    assert "Failed to validate GITHUB_TOKEN scopes" in str(exc_info.value)
    assert "Check your network connection" in exc_info.value.tip
