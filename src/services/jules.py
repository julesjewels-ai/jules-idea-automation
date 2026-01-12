import os
import requests
from typing import Optional, Dict, Any

class JulesAPIError(Exception):
    """Raised when the Jules API returns an error or cannot be reached."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class JulesClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        if not self.api_key:
            raise ValueError("JULES_API_KEY environment variable is not set")
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Internal method to handle API requests with unified error handling."""
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            # Try to extract error details from JSON response
            error_details = None
            message = str(e)
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_details = error_data["error"]
                    # Google APIs typically return {"error": {"message": "..."}}
                    if "message" in error_details:
                        message = error_details["message"]
            except ValueError:
                pass # Response was not JSON

            raise JulesAPIError(
                f"API Request Failed: {message}",
                status_code=e.response.status_code,
                details=error_details
            ) from e
        except requests.exceptions.RequestException as e:
            raise JulesAPIError(f"Network error: {str(e)}") from e

    def list_sources(self):
        """Lists available sources from Jules API."""
        url = f"{self.base_url}/sources"
        return self._request("GET", url)

    def create_session(self, source_id, prompt):
        """Creates a new session with the given source and prompt."""
        url = f"{self.base_url}/sessions"
        
        # Based on official API documentation:
        # https://developers.google.com/jules/api
        payload = {
            "prompt": prompt,
            "sourceContext": {
                "source": source_id,
                "githubRepoContext": {
                    "startingBranch": "main"
                }
            },
            "automationMode": "AUTO_CREATE_PR",
            "title": "Automated Idea Session"
        }
        
        return self._request("POST", url, json=payload)
    
    def source_exists(self, source_id):
        """Checks if a source exists in the user's connected sources."""
        sources = self.list_sources()
        for source in sources.get("sources", []):
            if source.get("name") == source_id:
                return True
        return False
    
    def get_session(self, session_id):
        """Retrieves details for a specific session.
        
        Args:
            session_id: The session ID (numeric string)
        
        Returns:
            Session object with outputs if complete
        """
        url = f"{self.base_url}/sessions/{session_id}"
        return self._request("GET", url)
    
    def list_sessions(self, page_size=10):
        """Lists recent sessions.
        
        Args:
            page_size: Number of sessions to return (default: 10)
        """
        url = f"{self.base_url}/sessions?pageSize={page_size}"
        return self._request("GET", url)
    
    def list_activities(self, session_id, page_size=30):
        """Lists activities (progress updates) for a session.
        
        Args:
            session_id: The session ID
            page_size: Number of activities to return (default: 30)
        """
        url = f"{self.base_url}/sessions/{session_id}/activities?pageSize={page_size}"
        return self._request("GET", url)
    
    def send_message(self, session_id, prompt):
        """Sends a follow-up message to an active session.
        
        Args:
            session_id: The session ID
            prompt: The message to send to the agent
        """
        url = f"{self.base_url}/sessions/{session_id}:sendMessage"
        payload = {"prompt": prompt}
        return self._request("POST", url, json=payload)
    
    def approve_plan(self, session_id):
        """Approves the pending plan for a session.
        
        Args:
            session_id: The session ID
        """
        url = f"{self.base_url}/sessions/{session_id}:approvePlan"
        return self._request("POST", url)
    
    def is_session_complete(self, session_id):
        """Checks if a session has completed and returns PR URL if available.
        
        Returns:
            tuple: (is_complete: bool, pr_url: str or None)
        """
        session = self.get_session(session_id)
        outputs = session.get("outputs", [])
        
        # Check for PR in outputs
        for output in outputs:
            if "pullRequest" in output:
                pr = output["pullRequest"]
                return True, pr.get("url")
        
        # Check activities for sessionCompleted
        activities = self.list_activities(session_id)
        for activity in activities.get("activities", []):
            if "sessionCompleted" in activity:
                # Session complete but might not have PR
                return True, None
        
        return False, None
