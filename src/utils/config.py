"""Startup configuration validation.

Checks that required API keys are present in the environment
before dispatching any CLI command, so users get a clear,
actionable summary of what's missing up front.
"""

from __future__ import annotations

import logging
import os

from src.utils.errors import ConfigurationError

logger = logging.getLogger(__name__)

# (env var name, setup URL)
_KEY_INFO: dict[str, str] = {
    "GEMINI_API_KEY": "https://aistudio.google.com/app/apikey",
    "GITHUB_TOKEN": "https://github.com/settings/tokens",
    "JULES_API_KEY": "https://jules.google.com",
}

# Which keys each command needs.
# Commands absent from this mapping require no keys (e.g. guide).
_COMMAND_KEYS: dict[str, list[str]] = {
    "agent": ["GEMINI_API_KEY", "GITHUB_TOKEN", "JULES_API_KEY"],
    "website": ["GEMINI_API_KEY", "GITHUB_TOKEN", "JULES_API_KEY"],
    "paste": ["GEMINI_API_KEY", "GITHUB_TOKEN", "JULES_API_KEY"],
    "manual": ["GEMINI_API_KEY", "GITHUB_TOKEN", "JULES_API_KEY"],
    "list-sources": ["JULES_API_KEY"],
    "status": ["JULES_API_KEY"],
    "preflight": [],
}

# Demo mode only needs Gemini — no GitHub or Jules interaction.
_DEMO_KEYS: list[str] = ["GEMINI_API_KEY"]


def validate_env_keys(command: str, *, is_demo: bool = False) -> None:
    """Validate that required API keys are set for the given command.

    Args:
    ----
        command: The CLI command name (e.g. "agent", "guide")
        is_demo: Whether --demo flag is active

    Raises:
    ------
        ConfigurationError: When one or more required keys are missing

    """
    if is_demo:
        required = _DEMO_KEYS
    else:
        required = _COMMAND_KEYS.get(command, [])

    if not required:
        return

    missing = [key for key in required if not os.environ.get(key)]

    if not missing:
        return

    # Build a status table
    lines: list[str] = []
    for key in required:
        if key in missing:
            lines.append(f"  {key:<20} ❌ Missing")
        else:
            lines.append(f"  {key:<20} ✅ Set")

    status_table = "\n".join(lines)

    # Build tips for missing keys only
    tips = "\n".join(f"  {key} → {_KEY_INFO[key]}" for key in missing)

    raise ConfigurationError(
        f"Missing required configuration:\n\n{status_table}",
        tip=f"Add the missing keys to your .env file:\n{tips}",
    )


def preflight_check_credentials(print_status: bool = False) -> None:
    """Verify Gemini, GitHub, and Jules API tokens are valid with lightweight pings.

    Call this before any expensive operations (e.g. Gemini API calls)
    to fail fast on expired or invalid tokens.

    Args:
    ----
        print_status: If True, prints status of each service check to stdout

    Raises:
    ------
        ConfigurationError: When a token is present but invalid/expired

    """
    errors: list[str] = []

    def _print_status(name: str, status: str) -> None:
        if print_status:
            print(f"  {name:<20} {status}")

    # Check Gemini token
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        _print_status("GEMINI_API_KEY", "❌ Missing")
    else:
        try:
            from src.services.gemini import GeminiClient

            next(iter(GeminiClient(api_key=gemini_key).client.models.list()))
            _print_status("GEMINI_API_KEY", "✅ Reachable")
        except Exception as exc:
            logger.debug("Gemini preflight failed: %s", exc)
            errors.append(
                "GEMINI_API_KEY is set but invalid or expired.\n  → Regenerate at https://aistudio.google.com/app/apikey"
            )
            _print_status("GEMINI_API_KEY", "❌ Invalid/Expired")

    # Check GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        _print_status("GITHUB_TOKEN", "❌ Missing")
    else:
        try:
            from src.services.github import GitHubClient

            GitHubClient(token=github_token).get_user()
            _print_status("GITHUB_TOKEN", "✅ Reachable")
        except Exception as exc:
            logger.debug("GitHub preflight failed: %s", exc)
            errors.append(
                "GITHUB_TOKEN is set but invalid or expired.\n  → Regenerate at https://github.com/settings/tokens"
            )
            _print_status("GITHUB_TOKEN", "❌ Invalid/Expired")

    # Check Jules token
    jules_key = os.environ.get("JULES_API_KEY")
    if not jules_key:
        _print_status("JULES_API_KEY", "❌ Missing")
    else:
        try:
            from src.services.jules import JulesClient

            JulesClient(api_key=jules_key).list_sources()
            _print_status("JULES_API_KEY", "✅ Reachable")
        except Exception as exc:
            logger.debug("Jules preflight failed: %s", exc)
            errors.append(
                "JULES_API_KEY is set but invalid or expired.\n  → Check your key at https://jules.google.com"
            )
            _print_status("JULES_API_KEY", "❌ Invalid/Expired")

    if errors:
        detail = "\n\n".join(errors)
        raise ConfigurationError(
            f"Credential check failed:\n\n{detail}",
            tip="Replace the invalid keys in your .env file and try again.",
        )
