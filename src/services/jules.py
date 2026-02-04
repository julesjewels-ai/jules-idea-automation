import os
import requests
from src.utils.errors import ConfigurationError, JulesApiError


class JulesClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "JULES_API_KEY environment variable is not set",
                tip="Ensure you have access to the Jules API and add the key "
                    "to your .env file."
            )
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _extract_api_error_message(self, response):
        """Extracts error message from Google-style JSON error response."""
        try:
            error_data = response.json()
            return error_data.get('error', {}).get('message')
        except Exception:
            return None

    def _handle_http_error(self, e):
        """Handles HTTP errors and raises JulesApiError with tips."""
        tip = None
        status_code = e.response.status_code

        if status_code == 401:
            tip = "Your Jules API key seems invalid. Check your .env file."
        elif status_code == 403:
            tip = "You don't have permission to access this resource."
        elif status_code == 404:
            tip = "The requested resource was not found."
        else:
            error_msg = self._extract_api_error_message(e.response)
            if error_msg:
                tip = f"API Message: {error_msg}"

            if not tip:
                tip = f"API returned status {status_code}."

        raise JulesApiError(f"Jules API Error: {e}", tip=tip)

    def _request(self, method: str, url: str, **kwargs):
        """Internal helper to handle API requests and errors."""
        try:
            response = requests.request(
                method, url, headers=self.headers, **kwargs
            )
            response.raise_for_status()

            # Some endpoints might not return content (e.g. 204), but
            # current usage suggests JSON
            if not response.text:
                return {}
            return response.json()

        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.RequestException as e:
            raise JulesApiError(
                f"Network error: {e}",
                tip="Check your internet connection."
            )

    def list_sources(self):
        """Lists available sources from Jules API."""
        return self._request("GET", f"{self.base_url}/sources")

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
        return self._request("GET", f"{self.base_url}/sessions/{session_id}")

    def list_sessions(self, page_size=10):
        """Lists recent sessions.

        Args:
            page_size: Number of sessions to return (default: 10)
        """
        return self._request(
            "GET",
            f"{self.base_url}/sessions",
            params={"pageSize": page_size}
        )

    def list_activities(self, session_id, page_size=30):
        """Lists activities (progress updates) for a session.

        Args:
            session_id: The session ID
            page_size: Number of activities to return (default: 30)
        """
        return self._request(
            "GET",
            f"{self.base_url}/sessions/{session_id}/activities",
            params={"pageSize": page_size}
        )

    def send_message(self, session_id, prompt):
        """Sends a follow-up message to an active session.

        Args:
            session_id: The session ID
            prompt: The message to send to the agent
        """
        return self._request(
            "POST",
            f"{self.base_url}/sessions/{session_id}:sendMessage",
            json={"prompt": prompt}
        )

    def approve_plan(self, session_id):
        """Approves the pending plan for a session.

        Args:
            session_id: The session ID
        """
        return self._request(
            "POST", f"{self.base_url}/sessions/{session_id}:approvePlan"
        )

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
