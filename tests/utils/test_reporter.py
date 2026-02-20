from src.utils.reporter import print_panel, strip_ansi, Colors


def test_print_panel_basic(capsys):
    print_panel("Hello", title="Test")
    captured = capsys.readouterr()
    assert "Hello" in captured.out
    assert "Test" in captured.out
    assert "╭" in captured.out  # Border char


def test_strip_ansi():
    text = f"{Colors.BOLD}Hello{Colors.ENDC}"
    assert strip_ansi(text) == "Hello"


def test_print_panel_no_title(capsys):
    print_panel("Content")
    captured = capsys.readouterr()
    assert "Content" in captured.out
    assert "─" in captured.out  # Top border without title


def test_print_panel_wrapping(capsys):
    long_text = "This is a very long text that should wrap around."
    width = 20  # Small width to force wrapping
    print_panel(long_text, width=width)
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    # Check that content lines are not longer than width + borders
    # 2 chars for borders + 2 chars for padding = 4 chars extra approx
    for line in lines:
        if "│" in line:
            assert len(strip_ansi(line)) <= width + 4
