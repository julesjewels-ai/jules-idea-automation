"""Shared HTTP client base class for API services."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.utils.errors import AppError

logger = logging.getLogger(__name__)

# Status codes that are safe to retry (transient server errors).
_RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})


class BaseApiClient:
    """Base class for HTTP API clients.

    Consolidates request execution, status-code error mapping, and
    JSON error-message extraction so that concrete clients (GitHub,
    Jules, etc.) only need to declare their endpoints and domain logic.

    All requests are automatically retried on transient failures
    (5xx status codes, timeouts, and connection errors) with
    exponential backoff.
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
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        self.base_url = base_url
        self.headers = headers
        self._error_class = error_class
        self._service_name = service_name
        self._status_tips: dict[int, str] = status_tips or {}
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Execute an HTTP request and return parsed JSON.

        Retries up to ``max_retries`` times on transient failures
        (5xx, Timeout, ConnectionError) with exponential backoff.
        Raises a domain-specific ``AppError`` subclass on permanent failure.
        """
        last_exception: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = requests.request(
                    method, url, headers=self.headers, timeout=self._timeout, **kwargs
                )
                response.raise_for_status()

                if not response.text:
                    return {}
                return response.json()  # type: ignore[no-any-return]

            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code in _RETRYABLE_STATUS_CODES:
                    last_exception = e
                    if attempt < self._max_retries:
                        delay = self._retry_base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "%s API returned %s (attempt %d/%d). Retrying in %.1fs…",
                            self._service_name,
                            e.response.status_code,
                            attempt,
                            self._max_retries,
                            delay,
                        )
                        time.sleep(delay)
                        continue
                    # Exhausted retries — fall through to raise
                else:
                    # 4xx errors are not retryable
                    tip = self._handle_http_error(e)
                    raise self._error_class(f"{self._service_name} API Error: {e}", tip=tip)

            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < self._max_retries:
                    delay = self._retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "%s request timed out (attempt %d/%d). Retrying in %.1fs…",
                        self._service_name,
                        attempt,
                        self._max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < self._max_retries:
                    delay = self._retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "%s connection error (attempt %d/%d). Retrying in %.1fs…",
                        self._service_name,
                        attempt,
                        self._max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue

            except requests.exceptions.RequestException as e:
                raise self._error_class(
                    f"Network error: {e}",
                    tip="Check your internet connection.",
                )

        # All retries exhausted
        if isinstance(last_exception, requests.exceptions.HTTPError):
            tip = self._handle_http_error(last_exception)
            raise self._error_class(
                f"{self._service_name} API Error after {self._max_retries} attempts: {last_exception}",
                tip=tip,
            )
        if isinstance(last_exception, requests.exceptions.Timeout):
            raise self._error_class(
                f"{self._service_name} request timed out after {self._max_retries} attempts",
                tip=f"The {self._service_name} API is not responding. Try again later.",
            )
        if isinstance(last_exception, requests.exceptions.ConnectionError):
            raise self._error_class(
                f"{self._service_name} connection failed after {self._max_retries} attempts: {last_exception}",
                tip="Check your internet connection.",
            )
        # Should never reach here, but satisfy type checker
        raise self._error_class(f"{self._service_name} request failed unexpectedly")

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
        return self._extract_api_error_message(e) or f"API returned status {status_code}."

    def _extract_api_error_message(self, e: requests.exceptions.HTTPError) -> str | None:
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
