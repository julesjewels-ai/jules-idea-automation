import os
import requests
from src.utils.errors import ConfigurationError, JulesApiError

class JulesClient:
    def __init__(self, api_key=None):
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

    def _request(self, method, endpoint, **kwargs):
        """Internal helper to make requests to the Jules API."""
        url = f"{self.base_url}/{endpoint}"

        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = 30

        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()

            # Return JSON if content exists, otherwise empty dict
            if not response.content:
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            # Try to parse error details from response
            status_code = e.response.status_code
            error_msg = str(e)
            tip = "Please check the Jules API documentation or try again later."

            try:
                error_data = e.response.json()
                if "error" in error_data:
                    # Google APIs often return error inside "error" object
                    err = error_data["error"]
                    if isinstance(err, dict):
                        error_msg = err.get("message", error_msg)
                    else:
                        error_msg = str(err)
            except Exception:
                pass # Use default string representation

            # Customize tips based on status code
            if status_code == 401:
                tip = "Check your JULES_API_KEY environment variable. It may be invalid or expired."
            elif status_code == 403:
                tip = "You do not have permission to access this resource. Check your project permissions."
            elif status_code == 404:
                tip = "The requested resource (session or source) was not found. Check the ID."
            elif status_code == 429:
                tip = "Rate limit exceeded. Please wait a moment before trying again."
            elif status_code >= 500:
                tip = "Jules API is experiencing internal issues. Please try again later."

            raise JulesApiError(f"Jules API Error ({status_code}): {error_msg}", tip=tip) from e

        except requests.exceptions.RequestException as e:
            raise JulesApiError(f"Network error connecting to Jules API: {e}",
                                tip="Check your internet connection and try again.") from e

    def list_sources(self):
        """Lists available sources from Jules API."""
        return self._request("GET", "sources")

    def create_session(self, source_id, prompt):
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
    
    def source_exists(self, source_id):
        """Checks if a source exists in the user's connected sources."""
        try:
            sources = self.list_sources()
            for source in sources.get("sources", []):
                if source.get("name") == source_id:
                    return True
            return False
        except JulesApiError:
            # If listing sources fails, we assume source check failed safely
            # or we could re-raise. For boolean check, re-raising is probably better
            # so the user knows something is wrong.
            raise
    
    def get_session(self, session_id):
        """Retrieves details for a specific session.
        
        Args:
            session_id: The session ID (numeric string)
        
        Returns:
            Session object with outputs if complete
        """
        return self._request("GET", f"sessions/{session_id}")
    
    def list_sessions(self, page_size=10):
        """Lists recent sessions.
        
        Args:
            page_size: Number of sessions to return (default: 10)
        """
        return self._request("GET", "sessions", params={"pageSize": page_size})
    
    def list_activities(self, session_id, page_size=30):
        """Lists activities (progress updates) for a session.
        
        Args:
            session_id: The session ID
            page_size: Number of activities to return (default: 30)
        """
        return self._request("GET", f"sessions/{session_id}/activities", params={"pageSize": page_size})
    
    def send_message(self, session_id, prompt):
        """Sends a follow-up message to an active session.
        
        Args:
            session_id: The session ID
            prompt: The message to send to the agent
        """
        payload = {"prompt": prompt}
        return self._request("POST", f"sessions/{session_id}:sendMessage", json=payload)
    
    def approve_plan(self, session_id):
        """Approves the pending plan for a session.
        
        Args:
            session_id: The session ID
        """
        return self._request("POST", f"sessions/{session_id}:approvePlan")
    
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
