"""GitHub API client."""

from __future__ import annotations

import base64
import os
from typing import Any

import requests

from src.utils.errors import ConfigurationError


class GitHubClient:
    """Client for GitHub API."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize the client."""
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

    def get_user(self) -> dict[str, Any]:
        """Return the authenticated user's details."""
        response = requests.get(f"{self.base_url}/user", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def create_repo(self, name: str, description: str, private: bool = True) -> dict[str, Any]:
        """Create a new repository."""
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False,  # We will add content manually
        }
        response = requests.post(f"{self.base_url}/user/repos", headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def create_file(self, owner: str, repo: str, path: str, content: str, message: str) -> dict[str, Any]:
        """Create or updates a file in the repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"

        # GitHub API requires content to be base64 encoded
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        payload = {"message": message, "content": encoded_content}

        response = requests.put(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def create_files(
        self, owner: str, repo: str, files: list[dict[str, str]], message: str, branch: str = "main"
    ) -> dict[str, Any]:
        """Create multiple files in a single commit using the Git Data API.

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
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()["object"]["sha"]  # type: ignore[no-any-return]

    def _get_tree_sha(self, owner: str, repo: str, commit_sha: str) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits/{commit_sha}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()["tree"]["sha"]  # type: ignore[no-any-return]

    def _create_blobs(self, owner: str, repo: str, files: list[dict[str, str]]) -> list[dict[str, Any]]:
        tree_items = []
        url = f"{self.base_url}/repos/{owner}/{repo}/git/blobs"
        for file_info in files:
            payload = {"content": file_info["content"], "encoding": "utf-8"}
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            tree_items.append(
                {"path": file_info["path"], "mode": "100644", "type": "blob", "sha": response.json()["sha"]}
            )
        return tree_items

    def _create_tree(self, owner: str, repo: str, base_tree_sha: str, tree_items: list[dict[str, Any]]) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees"
        payload = {"base_tree": base_tree_sha, "tree": tree_items}
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["sha"]  # type: ignore[no-any-return]

    def _create_commit(self, owner: str, repo: str, message: str, tree_sha: str, parents: list[str]) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits"
        payload = {"message": message, "tree": tree_sha, "parents": parents}
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["sha"]  # type: ignore[no-any-return]

    def _update_ref(self, owner: str, repo: str, branch: str, commit_sha: str) -> None:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        payload = {"sha": commit_sha}
        response = requests.patch(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
