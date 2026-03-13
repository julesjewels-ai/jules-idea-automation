from __future__ import annotations

import base64
import logging
import os
from typing import Any

import requests

from src.utils.errors import ConfigurationError, GitHubApiError

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ConfigurationError(
                "GITHUB_TOKEN environment variable is not set",
                tip="Create a Personal Access Token (PAT) with 'repo' scope at https://github.com/settings/tokens and add it to your .env file.",
            )
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Internal helper to handle API requests and errors."""
        try:
            response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            response.raise_for_status()

            if not response.text:
                return {}
            return response.json()  # type: ignore[no-any-return]

        except requests.exceptions.HTTPError as e:
            tip = self._handle_http_error(e)
            raise GitHubApiError(f"GitHub API Error: {e}", tip=tip)
        except requests.exceptions.Timeout:
            raise GitHubApiError(
                "GitHub API request timed out",
                tip="The GitHub API is taking too long to respond. Try again in a moment.",
            )
        except requests.exceptions.RequestException as e:
            raise GitHubApiError(f"Network error: {e}", tip="Check your internet connection.")

    def _handle_http_error(self, e: requests.exceptions.HTTPError) -> str:
        """Determines the appropriate user tip for an HTTP error."""
        status_code = e.response.status_code
        if status_code == 401:
            return "Your GitHub token seems invalid or expired. Check your .env file."
        if status_code == 403:
            return "You don't have permission. Your token may lack the required 'repo' scope."
        if status_code == 404:
            return "The requested resource was not found. Check repository name and owner."
        if status_code == 422:
            return self._extract_api_error_message(e) or "The request was invalid (422 Unprocessable Entity)."

        return self._extract_api_error_message(e) or f"API returned status {status_code}."

    def _extract_api_error_message(self, e: requests.exceptions.HTTPError) -> str | None:
        """Attempts to parse a GitHub JSON error message."""
        try:
            error_data = e.response.json()
            error_msg = error_data.get("message")
            if error_msg:
                return f"GitHub says: {error_msg}"
        except Exception:
            pass
        return None

    def get_user(self) -> dict[str, Any]:
        """Returns the authenticated user's details."""
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

            tree_items.append(
                {"path": file_info["path"], "mode": "100644", "type": "blob", "sha": data["sha"]}
            )
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
