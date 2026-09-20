from pathlib import Path


def test_ci_coverage_gate_configured():
    """Verify that the CI workflow includes the required coverage gate settings."""
    ci_path = Path(".github/workflows/ci.yml")
    assert ci_path.exists(), "CI workflow file missing"

    content = ci_path.read_text()

    assert "--cov-fail-under=70" in content, "Coverage threshold not set in CI"
    assert "actions/upload-artifact" in content, "Coverage artifact upload missing"
    assert "if: always()" in content, "Artifact upload step missing if: always()"
    assert "path: coverage.xml" in content, "Artifact upload path incorrect"


def test_dev_dependencies_configured():
    """Verify that pyproject.toml includes pytest-cov as a dev dependency."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml missing"

    content = pyproject_path.read_text()

    assert "[project.optional-dependencies]" in content, "Optional dependencies section missing"
    assert "pytest-cov==7.0.0" in content, "pytest-cov version constraint missing or incorrect"
