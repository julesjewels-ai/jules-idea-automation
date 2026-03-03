"""Unit tests for _normalize_requirements extracted helper."""

import pytest

from src.core.workflow import _normalize_requirements


class TestNormalizeRequirements:
    """Tests for the 4 LLM return-format branches."""

    def test_list_of_strings(self):
        """Standard expected format from Gemini."""
        result = _normalize_requirements(["pytest", "requests", "flask"])
        assert result == ["pytest", "requests", "flask"]

    def test_dict_with_versions(self):
        """Flash-model fallback format: {package: version_constraint}."""
        result = _normalize_requirements({
            "pytest": ">=7",
            "requests": "~=2.31",
        })
        assert result == ["pytest>=7", "requests~=2.31"]

    def test_dict_with_star_and_latest(self):
        """Star and 'latest' sentinels should be stripped."""
        result = _normalize_requirements({
            "pytest": "*",
            "flask": "latest",
            "requests": ">=2.0",
        })
        assert result == ["pytest", "flask", "requests>=2.0"]

    def test_list_of_dicts_package_version(self):
        """Unusual format: list of {package, version} dicts."""
        result = _normalize_requirements([
            {"package": "pytest", "version": ">=7"},
            {"package": "requests", "version": ""},
        ])
        assert result == ["pytest>=7", "requests"]

    def test_list_of_dicts_name_constraint(self):
        """Alternative dict keys: name and constraint."""
        result = _normalize_requirements([
            {"name": "flask", "constraint": ">=2.0"},
        ])
        assert result == ["flask>=2.0"]

    def test_mixed_list(self):
        """List mixing strings, dicts, and other types."""
        result = _normalize_requirements([
            "pytest",
            {"package": "flask", "version": ">=2"},
            42,
        ])
        assert result == ["pytest", "flask>=2", "42"]

    def test_scalar_string(self):
        """Edge case: single string requirement."""
        result = _normalize_requirements("pytest")
        assert result == ["pytest"]

    def test_scalar_non_string(self):
        """Edge case: non-string scalar."""
        result = _normalize_requirements(42)
        assert result == ["42"]

    def test_empty_list(self):
        """Empty list returns empty list."""
        result = _normalize_requirements([])
        assert result == []

    def test_empty_dict(self):
        """Empty dict returns empty list."""
        result = _normalize_requirements({})
        assert result == []
