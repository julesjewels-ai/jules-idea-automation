"""GitHub API client for repository management."""

from __future__ import annotations

import base64
import os
from typing import Any

import requests

from src.services.http_client import BaseApiClient
from src.utils.errors import ConfigurationError, GitHubApiError

_STATUS_TIPS: dict[int, str] = {
    401: "Your GitHub token seems invalid or expired. Check your .env file.",
    403: "Insufficient permissions. Check the scopes of your GitHub token.",
    404: "Resource not found. Check that the repository name is correct.",
}


class GitHubClient(BaseApiClient):
    """Client for GitHub API operations."""

    def __init__(self, token: str | None = None) -> None:
        token = token or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ConfigurationError(
                "GITHUB_TOKEN environment variable is not set",
                tip="Create a personal access token at https://github.com/settings/tokens and add it to your .env file.",
            )

        super().__init__(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            error_class=GitHubApiError,
            service_name="GitHub",
            status_tips=_STATUS_TIPS,
        )
        self._validate_token_scopes()

    def _validate_token_scopes(self) -> None:
        """Validates that the provided token has the required 'repo' scope."""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers=self.headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                raise ConfigurationError(
                    "GitHub token is invalid or expired.",
                    tip="Create a new personal access token at https://github.com/settings/tokens and update your .env file.",
                )
            # Other errors will be caught later or are transient
            return
        except requests.exceptions.RequestException:
            # Let network/timeout errors bubble up or be ignored during init
            return

        scopes = response.headers.get("x-oauth-scopes", "")
        scope_list = [s.strip() for s in scopes.split(",") if s.strip()]
        if "repo" not in scope_list:
            raise ConfigurationError(
                f"GitHub token is missing the required 'repo' scope. Current scopes: {scopes}",
                tip="Update your personal access token at https://github.com/settings/tokens to include the 'repo' scope.",
            )

    def get_user(self) -> dict[str, Any]:
        """Gets information about the authenticated user."""
        return self._request("GET", f"{self.base_url}/user")

    def create_repo(self, name: str, description: str, private: bool = True) -> dict[str, Any]:
        """Creates a new repository."""
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False,  # We will add content manually
        }
        return self._request("POST", f"{self.base_url}/user/repos", json=payload)

    def create_file(self, owner: str, repo: str, path: str, content: str, message: str) -> dict[str, Any]:
        """Creates or updates a file in the repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"

        # GitHub API requires content to be base64 encoded
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        payload = {"message": message, "content": encoded_content}

        return self._request("PUT", url, json=payload)

    def create_files(
        self, owner: str, repo: str, files: list[dict[str, str]], message: str, branch: str = "main"
    ) -> dict[str, Any]:
        """Creates multiple files in a single commit using the Git Data API.

        Args:
        ----
            owner: Repository owner
            repo: Repository name
            files: List of dicts with 'path' and 'content' keys
            message: Commit message
            branch: Target branch (default: main)

        """
        latest_commit_sha = self._get_latest_commit_sha(owner, repo, branch)
        base_tree_sha = self._get_tree_sha(owner, repo, latest_commit_sha)
        tree_items = self._create_blobs(owner, repo, files)
        new_tree_sha = self._create_tree(owner, repo, base_tree_sha, tree_items)
        new_commit_sha = self._create_commit(owner, repo, message, new_tree_sha, [latest_commit_sha])
        self._update_ref(owner, repo, branch, new_commit_sha)

        return {"commit_sha": new_commit_sha, "files_created": len(files)}

    def _get_latest_commit_sha(self, owner: str, repo: str, branch: str) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        data = self._request("GET", url)
        return data["object"]["sha"]  # type: ignore[no-any-return]

    def _get_tree_sha(self, owner: str, repo: str, commit_sha: str) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits/{commit_sha}"
        data = self._request("GET", url)
        return data["tree"]["sha"]  # type: ignore[no-any-return]

    def _create_blobs(self, owner: str, repo: str, files: list[dict[str, str]]) -> list[dict[str, Any]]:
        tree_items = []
        url = f"{self.base_url}/repos/{owner}/{repo}/git/blobs"
        for file_info in files:
            payload = {"content": file_info["content"], "encoding": "utf-8"}
            data = self._request("POST", url, json=payload)

            tree_items.append({"path": file_info["path"], "mode": "100644", "type": "blob", "sha": data["sha"]})
        return tree_items

    def _create_tree(self, owner: str, repo: str, base_tree_sha: str, tree_items: list[dict[str, Any]]) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees"
        payload = {"base_tree": base_tree_sha, "tree": tree_items}
        data = self._request("POST", url, json=payload)
        return data["sha"]  # type: ignore[no-any-return]

    def _create_commit(self, owner: str, repo: str, message: str, tree_sha: str, parents: list[str]) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits"
        payload = {"message": message, "tree": tree_sha, "parents": parents}
        data = self._request("POST", url, json=payload)
        return data["sha"]  # type: ignore[no-any-return]

    def _update_ref(self, owner: str, repo: str, branch: str, commit_sha: str) -> None:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        payload = {"sha": commit_sha}
        self._request("PATCH", url, json=payload)
