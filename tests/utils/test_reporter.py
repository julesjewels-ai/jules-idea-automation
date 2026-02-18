from src.utils.reporter import print_panel, strip_ansi, Colors


def test_print_panel_basic(capsys):
    """Test basic print_panel functionality."""
    content = "Hello World"
    title = "Test Title"
    width = 20

    print_panel(content, title=title, width=width, color=Colors.CYAN)

    captured = capsys.readouterr()
    output = captured.out

    # Verify title is present
    assert title in output

    # Verify content is present
    assert content in output

    # Verify width (approximately, by checking line lengths)
    # The output contains ANSI codes, so we should strip them for length checks
    clean_lines = [strip_ansi(line) for line in output.split('\n') if line.strip()]

    # Top border should contain the title
    assert title in clean_lines[0]

    # Content line should be enclosed in vertical bars
    content_line = [line for line in clean_lines if "Hello World" in line][0]
    assert content_line.startswith("│")
    assert content_line.endswith("│")

    # Verify visual width (allowing for some border chars)
    # Box drawing characters might mess up len() if not careful, but strip_ansi handles colors.
    # The printed width is effectively the 'width' parameter.
    # Top border length might vary slightly due to title placement logic but roughly matches width.
    assert len(clean_lines[0]) == width


def test_print_panel_wrapping(capsys):
    """Test print_panel wrapping functionality."""
    content = "This is a very long line that should be wrapped because it exceeds the width."
    width = 20  # Small width to force wrapping

    print_panel(content, width=width)

    captured = capsys.readouterr()
    output = captured.out
    clean_lines = [strip_ansi(line) for line in output.split('\n') if line.strip()]

    # Should have multiple content lines
    # Top border, bottom border, plus wrapped lines.
    # "This is a very long..." -> roughly 70 chars. Width 20 -> ~4-5 lines.
    assert len(clean_lines) > 3

    # Verify all lines respect width
    for line in clean_lines:
        assert len(line) <= width
