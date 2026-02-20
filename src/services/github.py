"""GitHub API Client."""

from __future__ import annotations
import os
import requests
import base64
from typing import Optional, Any
from src.utils.errors import ConfigurationError


class GitHubClient:
    """Client for GitHub API."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ConfigurationError(
                "GITHUB_TOKEN environment variable is not set",
                tip="Create a Personal Access Token (PAT) with 'repo' scope at "
                "https://github.com/settings/tokens and add it to your .env file."
            )

        self.api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_user(self) -> dict[str, Any]:
        """Get authenticated user details."""
        response = requests.get(f"{self.api_url}/user", headers=self.headers)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def create_repo(self, name: str, description: str, private: bool = False) -> dict[str, Any]:
        """Create a new repository."""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False  # We will add content manually
        }
        response = requests.post(f"{self.api_url}/user/repos", headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def create_file(self, owner: str, repo: str, path: str, content: str, message: str,
                    branch: str = "main") -> dict[str, Any]:
        """Create a new file in the repository."""
        url = f"{self.api_url}/repos/{owner}/{repo}/contents/{path}"
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": branch
        }
        response = requests.put(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def create_files(self, owner: str, repo: str, files: list[dict[str, str]],
                     message: str, branch: str = "main") -> dict[str, Any]:
        """Creates multiple files in a single commit using the Git Data API.

        Args:
            owner: Repository owner
            repo: Repository name
            files: List of dicts with 'path' and 'content' keys
            message: Commit message
            branch: Target branch (default: main)
        """
        # Get latest commit SHA
        ref_url = f"{self.api_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        ref_resp = requests.get(ref_url, headers=self.headers)
        ref_resp.raise_for_status()
        latest_commit_sha = ref_resp.json()["object"]["sha"]

        # Get tree SHA
        commit_url = f"{self.api_url}/repos/{owner}/{repo}/git/commits/{latest_commit_sha}"
        commit_resp = requests.get(commit_url, headers=self.headers)
        commit_resp.raise_for_status()
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        # Create blobs and build tree
        tree_items = []
        for file_info in files:
            # Create blob
            blob_data = {
                "content": file_info["content"],
                "encoding": "utf-8"
            }
            blob_resp = requests.post(
                f"{self.api_url}/repos/{owner}/{repo}/git/blobs",
                headers=self.headers,
                json=blob_data
            )
            blob_resp.raise_for_status()
            blob_sha = blob_resp.json()["sha"]

            tree_items.append({
                "path": file_info["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            })

        # Create new tree
        tree_data = {
            "base_tree": base_tree_sha,
            "tree": tree_items
        }
        tree_resp = requests.post(
            f"{self.api_url}/repos/{owner}/{repo}/git/trees",
            headers=self.headers,
            json=tree_data
        )
        tree_resp.raise_for_status()
        new_tree_sha = tree_resp.json()["sha"]

        # Create commit
        commit_data = {
            "message": message,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        }
        new_commit_resp = requests.post(
            f"{self.api_url}/repos/{owner}/{repo}/git/commits",
            headers=self.headers,
            json=commit_data
        )
        new_commit_resp.raise_for_status()
        new_commit_sha = new_commit_resp.json()["sha"]

        # Update reference
        update_ref_data = {
            "sha": new_commit_sha
        }
        update_resp = requests.patch(ref_url, headers=self.headers, json=update_ref_data)
        update_resp.raise_for_status()

        return {"files_created": len(files), "commit_sha": new_commit_sha}  # type: ignore[no-any-return]
