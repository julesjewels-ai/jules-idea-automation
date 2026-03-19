"""Shared HTTP client base class for API services."""

from __future__ import annotations

import logging
from typing import Any

import requests

from src.utils.errors import AppError

logger = logging.getLogger(__name__)


class BaseApiClient:
    """Base class for HTTP API clients.

    Consolidates request execution, status-code error mapping, and
    JSON error-message extraction so that concrete clients (GitHub,
    Jules, etc.) only need to declare their endpoints and domain logic.
    """

    def __init__(
        self,
        *,
        base_url: str,
        headers: dict[str, str],
        error_class: type[AppError],
        service_name: str,
        status_tips: dict[int, str] | None = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url
        self.headers = headers
        self._error_class = error_class
        self._service_name = service_name
        self._status_tips: dict[int, str] = status_tips or {}
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Execute an HTTP request and return parsed JSON.

        Raises a domain-specific ``AppError`` subclass on failure.
        """
        try:
            response = requests.request(
                method, url, headers=self.headers, timeout=self._timeout, **kwargs
            )
            response.raise_for_status()

            if not response.text:
                return {}
            return response.json()  # type: ignore[no-any-return]

        except requests.exceptions.HTTPError as e:
            tip = self._handle_http_error(e)
            raise self._error_class(f"{self._service_name} API Error: {e}", tip=tip)
        except requests.exceptions.Timeout:
            raise self._error_class(
                f"{self._service_name} request timed out",
                tip=f"The {self._service_name} API is not responding. Try again later.",
            )
        except requests.exceptions.RequestException as e:
            raise self._error_class(
                f"Network error: {e}",
                tip="Check your internet connection.",
            )

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _handle_http_error(self, e: requests.exceptions.HTTPError) -> str:
        """Determine the user-facing tip for an HTTP error.

        Checks ``_status_tips`` first, then falls back to the JSON
        error message or a generic status-code tip.
        """
        status_code = e.response.status_code

        # Subclass-specific overrides
        tip = self._status_tips.get(status_code)
        if tip:
            return tip

        # Try to extract a structured error message from the body
        return (
            self._extract_api_error_message(e) or f"API returned status {status_code}."
        )

    def _extract_api_error_message(
        self, e: requests.exceptions.HTTPError
    ) -> str | None:
        """Parse a JSON error body for a human-readable message.

        Supports two common layouts:
        - ``{"error": {"message": "…"}}``  (Google-style)
        - ``{"message": "…"}``             (GitHub-style)
        """
        try:
            data = e.response.json()
            # Google-style nested error
            nested = data.get("error", {})
            if isinstance(nested, dict):
                msg = nested.get("message")
                if msg:
                    return f"API Message: {msg}"
            # GitHub-style top-level message
            msg = data.get("message")
            if msg:
                return f"API Message: {msg}"
        except Exception:
            pass
        return None
