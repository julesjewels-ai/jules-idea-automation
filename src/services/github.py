"""GitHub API client service."""

import logging
import base64
from typing import Optional, Any
import requests
from src.utils.errors import APIError

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            token: GitHub PAT (read from env if None)
        """
        import os
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"

        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN is not set. Please set it in your .env file.\n"
                "Create a Personal Access Token (PAT) with 'repo' scope at https://github.com/settings/tokens"
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_user(self) -> dict[str, Any]:
        """Get authenticated user details."""
        url = f"{self.base_url}/user"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise APIError(f"GitHub API Error: {response.text}")

        return response.json()  # type: ignore

    def create_repo(self, name: str, description: str, private: bool = True) -> dict[str, Any]:
        """Create a new GitHub repository."""
        url = f"{self.base_url}/user/repos"
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False  # We will add content manually
        }

        response = requests.post(url, json=payload, headers=self.headers)

        if response.status_code == 422:
            # Check if repo already exists
            error_msg = response.json().get('message', '')
            if "name already exists" in error_msg:
                logger.warning(f"Repository '{name}' already exists. Using existing repo.")
                # Return existing repo details (simplified)
                user = self.get_user()
                return {"html_url": f"https://github.com/{user['login']}/{name}"}

        if response.status_code != 201:
            raise APIError(f"Failed to create GitHub repo: {response.text}")

        return response.json()  # type: ignore

    def create_files(
        self,
        owner: str,
        repo: str,
        files: list[dict[str, str]],
        message: str,
        branch: str = "main"
    ) -> dict[str, Any]:
        """Creates multiple files in a single commit using the Git Data API."""
        if not files:
            return {"files_created": 0}

        # 1. Get reference to latest commit on branch
        ref_url = f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        response = requests.get(ref_url, headers=self.headers)

        if response.status_code == 404:
            # Branch doesn't exist (empty repo), create initial commit?
            # For simplicity, we assume repo might be empty or initialized.
            # If empty, we can't use this flow easily without creating a root tree.
            # Fallback to create_file for the first file if needed, or handle empty repo case.
            pass

        # If we can't get ref (e.g. empty repo), we can't use tree API easily.
        # But wait, we initialized with auto_init=False, so it's empty.
        # However, we usually create README first using create_file which inits the repo.

        if response.status_code != 200:
            # Fallback: create files individually (slower but reliable for empty repos)
            created_count = 0
            for file in files:
                try:
                    self.create_file(owner, repo, file['path'], file['content'], message)
                    created_count += 1
                except APIError as e:
                    logger.warning(f"Failed to create file {file['path']}: {e}")
            return {"files_created": created_count}

        latest_commit_sha = response.json()["object"]["sha"]

        # 2. Get the tree for that commit
        commit_url = f"{self.base_url}/repos/{owner}/{repo}/git/commits/{latest_commit_sha}"
        commit_resp = requests.get(commit_url, headers=self.headers)
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        # 3. Create a new tree with new files
        tree_items = []
        for file in files:
            tree_items.append({
                "path": file['path'],
                "mode": "100644",
                "type": "blob",
                "content": file['content']
            })

        tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees"
        tree_payload = {
            "base_tree": base_tree_sha,
            "tree": tree_items
        }

        tree_resp = requests.post(tree_url, json=tree_payload, headers=self.headers)
        if tree_resp.status_code != 201:
            raise APIError(f"Failed to create git tree: {tree_resp.text}")

        new_tree_sha = tree_resp.json()["sha"]

        # 4. Create a new commit pointing to the new tree
        new_commit_url = f"{self.base_url}/repos/{owner}/{repo}/git/commits"
        commit_payload = {
            "message": message,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        }

        new_commit_resp = requests.post(new_commit_url, json=commit_payload, headers=self.headers)
        if new_commit_resp.status_code != 201:
            raise APIError(f"Failed to create git commit: {new_commit_resp.text}")

        new_commit_sha = new_commit_resp.json()["sha"]

        # 5. Update the reference to point to the new commit
        update_ref_url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        update_resp = requests.patch(update_ref_url, json={"sha": new_commit_sha}, headers=self.headers)

        if update_resp.status_code != 200:
            raise APIError(f"Failed to update git ref: {update_resp.text}")

        return {"files_created": len(files)}

    def create_file(self, owner: str, repo: str, path: str, content: str, message: str) -> dict[str, Any]:
        """Create a single file in the repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"

        # Encode content
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": message,
            "content": encoded_content
        }

        response = requests.put(url, json=payload, headers=self.headers)

        if response.status_code == 422:
            logger.warning(f"File '{path}' already exists or cannot be created.")
            return {}

        if response.status_code not in [200, 201]:
            raise APIError(f"Failed to create file '{path}': {response.text}")

        return response.json()  # type: ignore
