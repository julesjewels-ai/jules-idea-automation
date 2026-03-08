"""Client implementation for the Jules API."""

from __future__ import annotations

import os
from typing import Any

import requests

from src.utils.errors import ConfigurationError, JulesApiError


class JulesClient:
    """Client for interacting with the Jules API."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the JulesClient with an optional API key.

        Args:
            api_key: Optional Jules API key. Defaults to JULES_API_KEY env var.

        """
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "JULES_API_KEY environment variable is not set",
                tip="Ensure you have access to the Jules API and add the key to your .env file.",
            )
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Make an HTTP request and handle errors."""
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()

            # Some endpoints might not return content (e.g. 204), but current usage suggests JSON
            if not response.text:
                return {}
            return response.json()  # type: ignore[no-any-return]

        except requests.exceptions.HTTPError as e:
            tip = self._handle_http_error(e)
            raise JulesApiError(f"Jules API Error: {e}", tip=tip)
        except requests.exceptions.RequestException as e:
            raise JulesApiError(f"Network error: {e}", tip="Check your internet connection.")

    def _handle_http_error(self, e: requests.exceptions.HTTPError) -> str:
        """Determine the appropriate user tip for an HTTP error."""
        status_code = e.response.status_code
        if status_code == 401:
            return "Your Jules API key seems invalid. Check your .env file."
        if status_code == 403:
            return "You don't have permission to access this resource."
        if status_code == 404:
            return "The requested resource was not found."

        return self._extract_api_error_message(e) or f"API returned status {status_code}."

    def _extract_api_error_message(self, e: requests.exceptions.HTTPError) -> str | None:
        """Attempt to parse a Google-style JSON error message."""
        try:
            error_data = e.response.json()
            error_msg = error_data.get("error", {}).get("message")
            if error_msg:
                return f"API Message: {error_msg}"
        except Exception:
            pass
        return None

    def list_sources(self) -> dict[str, Any]:
        """List available sources from Jules API."""
        return self._request("GET", f"{self.base_url}/sources")

    def create_session(self, source_id: str, prompt: str) -> dict[str, Any]:
        """Create a new session with the given source and prompt."""
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
        """Check if a source exists in the user's connected sources."""
        sources = self.list_sources()
        for source in sources.get("sources", []):
            if source.get("name") == source_id:
                return True
        return False

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve details for a specific session.

        Args:
        ----
            session_id: The session ID (numeric string)

        Returns:
        -------
            Session object with outputs if complete

        """
        return self._request("GET", f"{self.base_url}/sessions/{session_id}")

    def list_sessions(self, page_size: int = 10) -> dict[str, Any]:
        """List recent sessions.

        Args:
        ----
            page_size: Number of sessions to return (default: 10)

        """
        return self._request("GET", f"{self.base_url}/sessions", params={"pageSize": page_size})

    def list_activities(self, session_id: str, page_size: int = 30) -> dict[str, Any]:
        """List activities (progress updates) for a session.

        Args:
        ----
            session_id: The session ID
            page_size: Number of activities to return (default: 30)

        """
        return self._request("GET", f"{self.base_url}/sessions/{session_id}/activities", params={"pageSize": page_size})

    def send_message(self, session_id: str, prompt: str) -> dict[str, Any]:
        """Send a follow-up message to an active session.

        Args:
        ----
            session_id: The session ID
            prompt: The message to send to the agent

        """
        return self._request("POST", f"{self.base_url}/sessions/{session_id}:sendMessage", json={"prompt": prompt})

    def approve_plan(self, session_id: str) -> dict[str, Any]:
        """Approve the pending plan for a session.

        Args:
        ----
            session_id: The session ID

        """
        return self._request("POST", f"{self.base_url}/sessions/{session_id}:approvePlan")

    def is_session_complete(self, session_id: str) -> tuple[bool, str | None]:
        """Check if a session has completed and return PR URL if available.

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
