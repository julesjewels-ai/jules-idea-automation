import os
import requests
import base64

class GitHubClient:
    def __init__(self, token=None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        self.base_url = "https://api.github.com"

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })

    def get_user(self):
        """Returns the authenticated user's details."""
        response = self.session.get(f"{self.base_url}/user")
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
        response = self.session.post(f"{self.base_url}/user/repos", json=payload)
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
        
        response = self.session.put(url, json=payload)
        response.raise_for_status()
        return response.json()

    def create_files(self, owner, repo, files, message, branch="main"):
        """Creates multiple files in a single commit using the Git Data API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            files: List of dicts with 'path' and 'content' keys
            message: Commit message
            branch: Target branch (default: main)
        """
        # Step 1: Get the latest commit SHA for the branch
        ref_url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        ref_response = self.session.get(ref_url)
        ref_response.raise_for_status()
        latest_commit_sha = ref_response.json()["object"]["sha"]
        
        # Step 2: Get the tree SHA from that commit
        commit_url = f"{self.base_url}/repos/{owner}/{repo}/git/commits/{latest_commit_sha}"
        commit_response = self.session.get(commit_url)
        commit_response.raise_for_status()
        base_tree_sha = commit_response.json()["tree"]["sha"]
        
        # Step 3: Create blobs for each file
        tree_items = []
        for file_info in files:
            blob_url = f"{self.base_url}/repos/{owner}/{repo}/git/blobs"
            blob_payload = {
                "content": file_info["content"],
                "encoding": "utf-8"
            }
            blob_response = self.session.post(blob_url, json=blob_payload)
            blob_response.raise_for_status()
            blob_sha = blob_response.json()["sha"]
            
            tree_items.append({
                "path": file_info["path"],
                "mode": "100644",  # Regular file
                "type": "blob",
                "sha": blob_sha
            })
        
        # Step 4: Create a new tree with all files
        tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees"
        tree_payload = {
            "base_tree": base_tree_sha,
            "tree": tree_items
        }
        tree_response = self.session.post(tree_url, json=tree_payload)
        tree_response.raise_for_status()
        new_tree_sha = tree_response.json()["sha"]
        
        # Step 5: Create a new commit pointing to the new tree
        new_commit_url = f"{self.base_url}/repos/{owner}/{repo}/git/commits"
        new_commit_payload = {
            "message": message,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        }
        new_commit_response = self.session.post(new_commit_url, json=new_commit_payload)
        new_commit_response.raise_for_status()
        new_commit_sha = new_commit_response.json()["sha"]
        
        # Step 6: Update the branch reference to point to the new commit
        update_ref_payload = {
            "sha": new_commit_sha
        }
        update_ref_response = self.session.patch(ref_url, json=update_ref_payload)
        update_ref_response.raise_for_status()
        
        return {
            "commit_sha": new_commit_sha,
            "files_created": len(files)
        }
