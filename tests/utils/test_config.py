"""Tests for startup configuration validation."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.utils.config import validate_env_keys
from src.utils.errors import ConfigurationError


# Helper to build a controlled env dict
def _env_with(**overrides: str) -> dict[str, str]:
    """Return a minimal env dict with only the specified keys."""
    return {k: v for k, v in overrides.items() if v is not None}


class TestValidateEnvKeys:
    """Tests for validate_env_keys()."""

    def test_guide_requires_no_keys(self) -> None:
        """The guide command needs no keys at all."""
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise
            validate_env_keys("guide")

    def test_agent_all_keys_present(self) -> None:
        """Agent command with all keys set passes validation."""
        env = _env_with(
            GEMINI_API_KEY="gk_test",
            GITHUB_TOKEN="ghp_test",
            JULES_API_KEY="jk_test",
        )
        with patch.dict(os.environ, env, clear=True):
            validate_env_keys("agent")

    def test_agent_missing_github_token(self) -> None:
        """Agent command missing GITHUB_TOKEN raises ConfigurationError."""
        env = _env_with(GEMINI_API_KEY="gk_test", JULES_API_KEY="jk_test")
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigurationError, match="GITHUB_TOKEN"):
                validate_env_keys("agent")

    def test_agent_demo_only_needs_gemini(self) -> None:
        """Demo mode only requires GEMINI_API_KEY."""
        env = _env_with(GEMINI_API_KEY="gk_test")
        with patch.dict(os.environ, env, clear=True):
            validate_env_keys("agent", is_demo=True)

    def test_agent_demo_missing_gemini(self) -> None:
        """Demo mode without GEMINI_API_KEY raises."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
                validate_env_keys("agent", is_demo=True)

    def test_status_only_needs_jules(self) -> None:
        """Status command only requires JULES_API_KEY."""
        env = _env_with(JULES_API_KEY="jk_test")
        with patch.dict(os.environ, env, clear=True):
            validate_env_keys("status")

    def test_status_missing_jules(self) -> None:
        """Status command without JULES_API_KEY raises."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError, match="JULES_API_KEY"):
                validate_env_keys("status")

    def test_all_keys_missing_lists_all(self) -> None:
        """When all keys are missing, error message lists all of them."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError, match="GEMINI_API_KEY") as exc_info:
                validate_env_keys("agent")
            msg = str(exc_info.value)
            assert "GITHUB_TOKEN" in msg
            assert "JULES_API_KEY" in msg

    def test_list_sources_only_needs_jules(self) -> None:
        """list-sources command only requires JULES_API_KEY."""
        env = _env_with(JULES_API_KEY="jk_test")
        with patch.dict(os.environ, env, clear=True):
            validate_env_keys("list-sources")

    def test_manual_needs_all_keys(self) -> None:
        """Manual command (non-demo) needs gemini + github + jules."""
        env = _env_with(
            GEMINI_API_KEY="gk_test",
            GITHUB_TOKEN="ghp_test",
            JULES_API_KEY="jk_test",
        )
        with patch.dict(os.environ, env, clear=True):
            validate_env_keys("manual")

    def test_unknown_command_requires_nothing(self) -> None:
        """An unrecognized command has no key requirements."""
        with patch.dict(os.environ, {}, clear=True):
            validate_env_keys("some-future-command")

    def test_error_tip_contains_urls(self) -> None:
        """The error tip should contain setup URLs for missing keys."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_env_keys("agent")
            assert exc_info.value.tip is not None
            assert "github.com/settings/tokens" in exc_info.value.tip
            assert "jules.google.com" in exc_info.value.tip
            assert "aistudio.google.com" in exc_info.value.tip


class TestPreflightCheckCredentials:
    """Tests for preflight_check_credentials()."""

    @patch("src.services.github.GitHubClient.get_user")
    @patch("src.services.jules.JulesClient.list_sources")
    @patch("google.genai.models.Models.list")
    def test_preflight_all_success(self, mock_gemini_list, mock_jules_list, mock_github_user) -> None:
        """When all credentials are valid, no error is raised."""
        mock_github_user.return_value = {"login": "testuser"}
        mock_jules_list.return_value = []
        mock_gemini_list.return_value = iter([{"name": "models/gemini-pro"}])

        env = _env_with(
            GEMINI_API_KEY="gk_test",
            GITHUB_TOKEN="ghp_test",
            JULES_API_KEY="jk_test",
        )
        with patch.dict(os.environ, env, clear=True):
            from src.utils.config import preflight_check_credentials

            # Should not raise
            preflight_check_credentials()

    @patch("google.genai.models.Models.list")
    def test_preflight_gemini_failure(self, mock_gemini_list) -> None:
        """When Gemini API fails, ConfigurationError is raised with a clear message."""
        mock_gemini_list.side_effect = Exception("API Key invalid")

        env = _env_with(GEMINI_API_KEY="gk_bad")
        with patch.dict(os.environ, env, clear=True):
            from src.utils.config import preflight_check_credentials

            with pytest.raises(ConfigurationError, match="Credential check failed") as exc_info:
                preflight_check_credentials()

            assert "GEMINI_API_KEY" in str(exc_info.value)
            assert "invalid or expired" in str(exc_info.value)
