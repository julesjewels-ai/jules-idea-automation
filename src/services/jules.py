import os
import requests
from typing import Optional, Dict, Any, Tuple
from src.utils.errors import ConfigurationError, AppError

class JulesClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "JULES_API_KEY environment variable is not set",
                tip="Ensure you have access to the Jules API and add the key to your .env file."
            )
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Internal helper to handle API requests and errors."""
        try:
            response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 0

            if status_code == 401:
                tip = "Your JULES_API_KEY appears to be invalid or expired. Check your .env file."
            elif status_code == 403:
                tip = "You do not have permission to access this resource. Check if the 'Jules API' is enabled in Google Cloud Console."
            elif status_code == 404:
                tip = "The requested resource was not found. If this is a source, ensure the repository is connected."
            elif status_code >= 500:
                tip = "Jules API is currently experiencing issues. Please try again later."
            else:
                tip = f"API returned {status_code}: {e.response.text if e.response is not None else 'Unknown error'}"

            raise AppError(f"Jules API Error: {e}", tip=tip) from e

        except requests.exceptions.ConnectionError as e:
            raise AppError(
                f"Connection failed: {e}",
                tip="Check your internet connection and try again."
            ) from e
        except requests.exceptions.Timeout as e:
            raise AppError(
                f"Request timed out: {e}",
                tip="The Jules API took too long to respond. Please try again later."
            ) from e
        except requests.exceptions.RequestException as e:
            raise AppError(
                f"An unexpected error occurred: {e}",
                tip="Please check your network settings or report this issue."
            ) from e

    def list_sources(self) -> Dict[str, Any]:
        """Lists available sources from Jules API."""
        url = f"{self.base_url}/sources"
        return self._request("GET", url)

    def create_session(self, source_id: str, prompt: str) -> Dict[str, Any]:
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
    
    def source_exists(self, source_id: str) -> bool:
        """Checks if a source exists in the user's connected sources."""
        try:
            sources = self.list_sources()
            for source in sources.get("sources", []):
                if source.get("name") == source_id:
                    return True
            return False
        except AppError:
            # Propagate error if listing sources fails significantly
            # But if it's just empty/404, maybe return False?
            # For now, let's allow it to propagate so the user knows why.
            raise

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieves details for a specific session.
        
        Args:
            session_id: The session ID (numeric string)
        
        Returns:
            Session object with outputs if complete
        """
        url = f"{self.base_url}/sessions/{session_id}"
        return self._request("GET", url)
    
    def list_sessions(self, page_size: int = 10) -> Dict[str, Any]:
        """Lists recent sessions.
        
        Args:
            page_size: Number of sessions to return (default: 10)
        """
        url = f"{self.base_url}/sessions?pageSize={page_size}"
        return self._request("GET", url)
    
    def list_activities(self, session_id: str, page_size: int = 30) -> Dict[str, Any]:
        """Lists activities (progress updates) for a session.
        
        Args:
            session_id: The session ID
            page_size: Number of activities to return (default: 30)
        """
        url = f"{self.base_url}/sessions/{session_id}/activities?pageSize={page_size}"
        return self._request("GET", url)
    
    def send_message(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """Sends a follow-up message to an active session.
        
        Args:
            session_id: The session ID
            prompt: The message to send to the agent
        """
        url = f"{self.base_url}/sessions/{session_id}:sendMessage"
        payload = {"prompt": prompt}
        return self._request("POST", url, json=payload)
    
    def approve_plan(self, session_id: str) -> Dict[str, Any]:
        """Approves the pending plan for a session.
        
        Args:
            session_id: The session ID
        """
        url = f"{self.base_url}/sessions/{session_id}:approvePlan"
        return self._request("POST", url)
    
    def is_session_complete(self, session_id: str) -> Tuple[bool, Optional[str]]:
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
