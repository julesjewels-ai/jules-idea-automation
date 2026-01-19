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

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Helper to handle API requests and errors."""
        url = f"{self.base_url}/{endpoint}"
        # Set default timeout if not provided
        kwargs.setdefault("timeout", 30)

        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()

            # Handle empty response (e.g. 204 No Content or just empty body)
            if not response.text:
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status == 401:
                raise AppError(
                    "Jules API Authentication Failed",
                    tip="Check your JULES_API_KEY in .env. It might be invalid or expired."
                )
            elif status == 403:
                raise AppError(
                    "Jules API Permission Denied",
                    tip="Your API key doesn't have access to this resource. Ensure the API is enabled in your Google Cloud Project."
                )
            elif status == 404:
                raise AppError(
                    f"Resource Not Found: {endpoint}",
                    tip="The session or source ID might be incorrect."
                )
            elif status >= 500:
                raise AppError(
                    f"Jules API Server Error ({status})",
                    tip="The Jules service is experiencing issues. Please try again later."
                )
            else:
                raise AppError(
                    f"Jules API Error: {status}",
                    tip=f"Request failed: {e}"
                )
        except requests.exceptions.ConnectionError:
            raise AppError(
                "Jules API Connection Failed",
                tip="Check your internet connection and try again."
            )
        except requests.exceptions.Timeout:
            raise AppError(
                "Jules API Request Timed Out",
                tip="The request took too long. The service might be slow or down."
            )
        except requests.exceptions.RequestException as e:
            raise AppError(
                "Jules API Request Failed",
                tip=f"An unexpected network error occurred: {e}"
            )

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
