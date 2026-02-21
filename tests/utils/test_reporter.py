from src.utils.reporter import print_panel, strip_ansi, Colors


def test_print_panel_basic(capsys):
    """Test basic print_panel functionality."""
    content = "Hello World"
    print_panel(content, title="Title")
    captured = capsys.readouterr()

    assert "╭" in captured.out
    assert "Title" in captured.out
    assert "Hello World" in captured.out


def test_print_panel_wrapping(capsys):
    content = "This is a very long line that should be wrapped because it exceeds the panel width."
    width = 20  # Small width to force wrapping

    print_panel(content, width=width)
    captured = capsys.readouterr()

    # Check that output width doesn't exceed limit significantly
    lines = captured.out.split('\n')
    # Filter out empty lines
    lines = [line for line in lines if line.strip()]

    # Verify wrapping occurred (multiple lines of content)
    content_lines = [line for line in lines if "│" in line]
    assert len(content_lines) > 1

    # Check content is present (partial match on first chunk)
    assert "This is a very" in captured.out


def test_strip_ansi():
    """Test ANSI stripping."""
    text = f"{Colors.RED}Hello{Colors.ENDC}"
    assert strip_ansi(text) == "Hello"
