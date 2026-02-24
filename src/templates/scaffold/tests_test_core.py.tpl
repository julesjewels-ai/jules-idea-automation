"""Tests for core application."""

from src.core.app import App


def test_app_init() -> None:
    """Test app initialization."""
    app = App()
    assert app.name == "{title}"


def test_app_run(capsys) -> None:
    """Test app run output."""
    app = App()
    app.run()
    captured = capsys.readouterr()
    assert "Welcome to" in captured.out
