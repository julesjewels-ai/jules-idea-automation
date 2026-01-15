import os
import requests
from typing import Optional, Any

class JulesAPIError(Exception):
    """Custom exception for Jules API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[Status {self.status_code}] {self.message}"
        return self.message


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

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Internal helper to make API requests with better error handling."""
        url = f"{self.base_url}/{endpoint}"

        # Merge headers if needed
        headers = self.headers.copy()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.HTTPError as e:
            # Try to parse the error response
            error_msg = str(e)
            details = None
            status_code = e.response.status_code if e.response is not None else None

            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_info = error_data["error"]
                    if isinstance(error_info, dict):
                        # Handle Google API error format
                        # { "error": { "code": 403, "message": "...", "status": "..." } }
                        server_msg = error_info.get("message")
                        status = error_info.get("status")

                        if server_msg:
                            error_msg = server_msg
                        if status:
                            error_msg += f" ({status})"

                        details = error_info
                    elif isinstance(error_info, str):
                        error_msg = error_info
            except ValueError:
                # Response was not JSON, stick to default error
                pass

            raise JulesAPIError(error_msg, status_code=status_code, details=details) from e

        except requests.exceptions.RequestException as e:
            raise JulesAPIError(f"Network error: {str(e)}") from e

    def list_sources(self) -> dict:
        """Lists available sources from Jules API."""
        return self._request("GET", "sources")

    def create_session(self, source_id: str, prompt: str) -> dict:
        """Creates a new session with the given source and prompt."""
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
        
        return self._request("POST", "sessions", json=payload)
    
    def source_exists(self, source_id: str) -> bool:
        """Checks if a source exists in the user's connected sources."""
        sources = self.list_sources()
        for source in sources.get("sources", []):
            if source.get("name") == source_id:
                return True
        return False
    
    def get_session(self, session_id: str) -> dict:
        """Retrieves details for a specific session.
        
        Args:
            session_id: The session ID (numeric string)
        
        Returns:
            Session object with outputs if complete
        """
        return self._request("GET", f"sessions/{session_id}")
    
    def list_sessions(self, page_size: int = 10) -> dict:
        """Lists recent sessions.
        
        Args:
            page_size: Number of sessions to return (default: 10)
        """
        return self._request("GET", f"sessions?pageSize={page_size}")
    
    def list_activities(self, session_id: str, page_size: int = 30) -> dict:
        """Lists activities (progress updates) for a session.
        
        Args:
            session_id: The session ID
            page_size: Number of activities to return (default: 30)
        """
        return self._request("GET", f"sessions/{session_id}/activities?pageSize={page_size}")
    
    def send_message(self, session_id: str, prompt: str) -> dict:
        """Sends a follow-up message to an active session.
        
        Args:
            session_id: The session ID
            prompt: The message to send to the agent
        """
        payload = {"prompt": prompt}
        return self._request("POST", f"sessions/{session_id}:sendMessage", json=payload)
    
    def approve_plan(self, session_id: str) -> dict:
        """Approves the pending plan for a session.
        
        Args:
            session_id: The session ID
        """
        return self._request("POST", f"sessions/{session_id}:approvePlan")
    
    def is_session_complete(self, session_id: str) -> tuple[bool, Optional[str]]:
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
