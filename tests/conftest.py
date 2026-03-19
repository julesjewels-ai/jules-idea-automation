from __future__ import annotations

import os
import sys
from typing import Any
from unittest.mock import MagicMock

import requests

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def make_http_error(status_code: int, body: dict[str, Any] | None = None) -> requests.exceptions.HTTPError:
    """Factory for HTTPError with a mock response.

    Shared across test_github.py and test_jules.py.
    """
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body or {}
    return requests.exceptions.HTTPError(response=response)


def make_ok_response(json_data: Any, status_code: int = 200) -> MagicMock:
    """Factory for successful mock responses."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.text = "{}"
    resp.raise_for_status.return_value = None
    return resp
