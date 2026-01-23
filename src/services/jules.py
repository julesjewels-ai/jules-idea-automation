import os
import requests
from src.utils.errors import ConfigurationError, AppError

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
        """Helper to make requests with centralized error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()

            # Return JSON if content exists, otherwise empty dict
            return response.json() if response.text else {}

        except requests.exceptions.ConnectionError:
            raise AppError(
                "Unable to connect to Jules API.",
                tip="Check your internet connection and ensure the API is accessible."
            )
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code

            if status_code == 401:
                raise ConfigurationError(
                    "Authentication failed: Invalid API Key.",
                    tip="Check your JULES_API_KEY in .env file."
                )
            elif status_code == 403:
                raise ConfigurationError(
                    "Access denied: You don't have permission to access this resource.",
                    tip="Ensure your API key has the necessary scopes and quotas."
                )
            elif status_code == 404:
                raise AppError(
                    f"Resource not found: {endpoint}",
                    tip="The requested source or session ID might be incorrect."
                )
            elif 500 <= status_code < 600:
                raise AppError(
                    "Jules API encountered a server error.",
                    tip="This is likely temporary. Please try again later."
                )
            else:
                raise AppError(
                    f"Jules API Error ({status_code}): {e.response.text}",
                    tip="Review the error message for details."
                )
        except requests.exceptions.RequestException as e:
            raise AppError(
                f"An unexpected network error occurred: {e}",
                tip="Check your network configuration."
            )

    def list_sources(self):
        """Lists available sources from Jules API."""
        return self._request("GET", "/sources")

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
        
        return self._request("POST", "/sessions", json=payload)
    
    def source_exists(self, source_id):
        """Checks if a source exists in the user's connected sources."""
        # indirect call, errors bubble up from list_sources
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
        return self._request("GET", f"/sessions/{session_id}")
    
    def list_sessions(self, page_size=10):
        """Lists recent sessions.
        
        Args:
            page_size: Number of sessions to return (default: 10)
        """
        return self._request("GET", f"/sessions?pageSize={page_size}")
    
    def list_activities(self, session_id, page_size=30):
        """Lists activities (progress updates) for a session.
        
        Args:
            session_id: The session ID
            page_size: Number of activities to return (default: 30)
        """
        return self._request("GET", f"/sessions/{session_id}/activities?pageSize={page_size}")
    
    def send_message(self, session_id, prompt):
        """Sends a follow-up message to an active session.
        
        Args:
            session_id: The session ID
            prompt: The message to send to the agent
        """
        return self._request("POST", f"/sessions/{session_id}:sendMessage", json={"prompt": prompt})
    
    def approve_plan(self, session_id):
        """Approves the pending plan for a session.
        
        Args:
            session_id: The session ID
        """
        return self._request("POST", f"/sessions/{session_id}:approvePlan")
    
    def is_session_complete(self, session_id):
        """Checks if a session has completed and returns PR URL if available.
        
        Returns:
            tuple: (is_complete: bool, pr_url: str or None)
        """
        # indirect call, errors bubble up from get_session/list_activities
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
