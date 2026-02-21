"""Tests for reporter utility."""

from src.utils.reporter import (
    strip_ansi,
    _create_top_border,
    Colors,
    print_panel
)


def test_strip_ansi():
    """Test ANSI code stripping."""
    text = f"{Colors.RED}Hello{Colors.ENDC}"
    assert strip_ansi(text) == "Hello"


def test_create_top_border_no_title():
    """Test top border creation without title."""
    width = 10
    border = _create_top_border("", width, "")
    # ╭────────╮
    assert len(strip_ansi(border)) == width


def test_create_top_border_with_title():
    """Test top border with title."""
    width = 20
    title = "Test"
    border = _create_top_border(title, width, "")
    # ╭── Test ──────────╮ (approx)
    assert "Test" in border
    assert len(strip_ansi(border)) == width


def test_create_top_border_long_title():
    """Test top border with truncated title."""
    width = 10
    title = "VeryLongTitle"
    border = _create_top_border(title, width, "")
    assert "…" in border
    assert len(strip_ansi(border)) == width


def test_print_panel_basic(capsys):
    """Test basic panel printing."""
    content = "Hello World"
    print_panel(content, width=20)
    captured = capsys.readouterr()
    assert "Hello World" in captured.out
    assert "╭" in captured.out
    assert "╰" in captured.out


def test_print_panel_wrapping(capsys):
    """Test panel content wrapping."""
    content = "This is a very long line that should wrap inside the panel"
    width = 20  # Small width to force wrapping
    print_panel(content, width=width)
    captured = capsys.readouterr()

    # Check that output contains broken parts of the string
    assert "This is a" in captured.out

    # Check width of lines (approximate check)
    lines = captured.out.split('\n')
    # Filter out empty lines
    panel_lines = [line for line in lines if "│" in line]
    for line in panel_lines:
        # Visual width check is tricky with ANSI codes, but strip_ansi helps
        # The printed width might vary slightly due to implementation details,
        # but shouldn't exceed width significantly (ignoring ANSI)
        assert len(strip_ansi(line)) <= width + 5  # Allow some margin for border chars
