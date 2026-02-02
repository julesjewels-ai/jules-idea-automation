"""
Smoke Tests

Basic tests to verify the test harness and core imports work.
These should always pass - they verify the foundation is stable.

Mason/Coder: Add domain-specific tests in tests/unit/ and tests/integration/
"""

import pytest


class TestSmoke:
    """Smoke tests to verify test infrastructure works."""
    
    def test_harness_runs(self):
        """Verify pytest can run a basic test."""
        assert True
    
    def test_core_imports(self):
        """Verify core module can be imported."""
        import src
        import src.core
        assert src is not None
        assert src.core is not None
    
    def test_interfaces_defined(self):
        """Verify interfaces module has expected ABCs."""
        from src.core.interfaces import IdeaSource, RepositoryCreator, SessionManager
        
        # Verify they are abstract
        from abc import ABC
        assert issubclass(IdeaSource, ABC)
        assert issubclass(RepositoryCreator, ABC)
        assert issubclass(SessionManager, ABC)


class TestEnvironment:
    """Verify development environment is correctly configured."""
    
    def test_python_version(self):
        """Verify Python version meets requirements."""
        import sys
        assert sys.version_info >= (3, 9), "Python 3.9+ required"
    
    @pytest.mark.skip(reason="Dependencies may not be installed in CI")
    def test_dependencies_available(self):
        """Verify key dependencies can be imported."""
        import click
        import pydantic
        assert click is not None
        assert pydantic is not None
