import os
import requests
import base64

class GitHubClient:
    def __init__(self, token=None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_user(self):
        """Returns the authenticated user's details."""
        response = requests.get(f"{self.base_url}/user", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_repo(self, name, description, private=True):
        """Creates a new repository."""
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False # We will add content manually
        }
        response = requests.post(f"{self.base_url}/user/repos", headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def create_file(self, owner, repo, path, content, message):
        """Creates or updates a file in the repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        # GitHub API requires content to be base64 encoded
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": message,
            "content": encoded_content
        }
        
        response = requests.put(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
