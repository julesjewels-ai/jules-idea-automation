"""Test that CI coverage gates are configured correctly."""

import os
from pathlib import Path

def test_coverage_gate_configured_in_pyproject() -> None:
    """Verify that pyproject.toml contains the required test coverage flags."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"

    content = pyproject_path.read_text()

    assert "--cov=src" in content, "Missing src coverage flag"
    assert "--cov=main" in content, "Missing main coverage flag"
    assert "--cov-fail-under=70" in content, "Missing coverage threshold flag (70%)"
    assert "--cov-report=xml" in content, "Missing XML coverage report flag"

def test_coverage_artifact_in_ci_workflow() -> None:
    """Verify that the CI workflow uploads the coverage report artifact."""
    ci_path = Path(".github/workflows/ci.yml")
    assert ci_path.exists(), ".github/workflows/ci.yml not found"

    content = ci_path.read_text()

    assert "uses: actions/upload-artifact" in content, "Missing artifact upload step"
    assert "name: coverage-report" in content, "Artifact name is not coverage-report"
    assert "path: coverage.xml" in content, "Artifact path is not coverage.xml"
