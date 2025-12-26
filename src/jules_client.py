import os
import requests

class JulesClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        if not self.api_key:
            raise ValueError("JULES_API_KEY environment variable is not set")
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def list_sources(self):
        """Lists available sources from Jules API."""
        url = f"{self.base_url}/sources"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_session(self, source_id, prompt):
        """Creates a new session with the given source and prompt."""
        url = f"{self.base_url}/sessions"
        
        # Based on documentation:
        # sourceContext requires "source" and "githubRepoContext" (if it's a github repo)
        # However, list_sources returns the full source name/id.
        # The prompt payload structure:
        # {
        #   "prompt": "...",
        #   "sourceContext": {
        #      "source": "sources/github/owner/repo",
        #      "githubRepoContext": { "startingBranch": "main" }
        #   }
        # }
        # I'll assume standard defaults for now or try to infer from source_id if needed.
        # But for simplicity, let's assume source_id passed here is the full resource name e.g. "sources/github/..."
        
        payload = {
            "prompt": prompt,
            "sourceContext": {
                "source": source_id,
                # We might need to make this dynamic if the user wants to specify branch, 
                # but for now hardcoding 'main' is a reasonable default for an MVP unless the source metadata tells us otherwise.
                "githubRepoContext": {
                    "startingBranch": "main"
                }
            },
             # "automationMode": "AUTO_CREATE_PR", # Optional, maybe leave out for now or add as a flag later
            "title": "Automated Idea Session"
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
