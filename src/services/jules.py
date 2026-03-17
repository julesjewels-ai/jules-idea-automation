"""Jules API client for session management."""

from __future__ import annotations

import os
from typing import Any

from src.services.http_client import BaseApiClient
from src.utils.errors import ConfigurationError, JulesApiError

_STATUS_TIPS: dict[int, str] = {
    401: "Your Jules API key seems invalid. Check your .env file.",
    403: "You don't have permission to access this resource.",
    404: "The requested resource was not found.",
}


class JulesClient(BaseApiClient):
    """Client for Jules API operations."""

    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or os.environ.get("JULES_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "JULES_API_KEY environment variable is not set",
                tip="Ensure you have access to the Jules API and add the key to your .env file.",
            )

        super().__init__(
            base_url="https://jules.googleapis.com/v1alpha",
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            error_class=JulesApiError,
            service_name="Jules",
            status_tips=_STATUS_TIPS,
        )

    def list_sources(self) -> dict[str, Any]:
        """Lists available sources from Jules API."""
        return self._request("GET", f"{self.base_url}/sources")

    def create_session(self, source_id: str, prompt: str) -> dict[str, Any]:
        """Creates a new session with the given source and prompt."""
        url = f"{self.base_url}/sessions"

        # Based on official API documentation:
        # https://developers.google.com/jules/api
        payload = {
            "prompt": prompt,
            "sourceContext": {"source": source_id, "githubRepoContext": {"startingBranch": "main"}},
            "automationMode": "AUTO_CREATE_PR",
            "title": "Automated Idea Session",
        }

        return self._request("POST", url, json=payload)

    def source_exists(self, source_id: str) -> bool:
        """Checks if a source exists in the user's connected sources."""
        sources = self.list_sources()
        for source in sources.get("sources", []):
            if source.get("name") == source_id:
                return True
        return False

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Retrieves details for a specific session.

        Args:
        ----
            session_id: The session ID (numeric string)

        Returns:
        -------
            Session object with outputs if complete

        """
        return self._request("GET", f"{self.base_url}/sessions/{session_id}")

    def list_sessions(self, page_size: int = 10) -> dict[str, Any]:
        """Lists recent sessions.

        Args:
        ----
            page_size: Number of sessions to return (default: 10)

        """
        return self._request("GET", f"{self.base_url}/sessions", params={"pageSize": page_size})

    def list_activities(self, session_id: str, page_size: int = 30) -> dict[str, Any]:
        """Lists activities (progress updates) for a session.

        Args:
        ----
            session_id: The session ID
            page_size: Number of activities to return (default: 30)

        """
        return self._request("GET", f"{self.base_url}/sessions/{session_id}/activities", params={"pageSize": page_size})

    def send_message(self, session_id: str, prompt: str) -> dict[str, Any]:
        """Sends a follow-up message to an active session.

        Args:
        ----
            session_id: The session ID
            prompt: The message to send to the agent

        """
        return self._request("POST", f"{self.base_url}/sessions/{session_id}:sendMessage", json={"prompt": prompt})

    def approve_plan(self, session_id: str) -> dict[str, Any]:
        """Approves the pending plan for a session.

        Args:
        ----
            session_id: The session ID

        """
        return self._request("POST", f"{self.base_url}/sessions/{session_id}:approvePlan")

    def is_session_complete(self, session_id: str) -> tuple[bool, str | None]:
        """Checks if a session has completed and returns PR URL if available.

        Returns
        -------
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
