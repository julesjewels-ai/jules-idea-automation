"""Jules API Client."""
import os
import requests

class JulesClient:
    """Client for interacting with the Jules API."""

    def __init__(self, api_key=None, timeout=30):
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        if not self.api_key:
            raise ValueError("JULES_API_KEY environment variable is not set")
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.timeout = timeout

    def _request(self, method, endpoint, **kwargs):
        """Helper method to handle API requests."""
        url = f"{self.base_url}/{endpoint}"
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        # pylint: disable=missing-timeout
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json() if response.text else {}

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
        return self._request(
            "GET",
            f"sessions/{session_id}/activities",
            params={"pageSize": page_size}
        )

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
