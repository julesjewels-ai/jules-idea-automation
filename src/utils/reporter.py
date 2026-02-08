"""Console reporting utilities."""

import sys
import time
import threading
import re
from types import TracebackType
from typing import Optional, Any, Type


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def strip_ansi(text: str) -> str:
    """Removes ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def _create_top_border(title: str, width: int, color: str) -> str:
    # Box drawing characters
    H_LINE = "─"
    TL_CORNER = "╭"
    TR_CORNER = "╮"

    if not title:
        return f"{TL_CORNER}{H_LINE * (width - 2)}{TR_CORNER}"

    title_text = f" {title} "

    # Check for emojis to adjust padding for visual consistency (best effort)
    # Assuming common emojis are 2 chars wide but length 1
    # This is not perfect but improves the most common case in this app (✨)
    visual_offset = 0
    if "✨" in title:
        visual_offset += 1

    # Ensure title fits
    if len(title_text) > width - 4:
        title_text = title_text[:width-5] + "…"

    left_pad = 2
    # Adjust right pad calculation by subtracting visual offset from the available space
    # (wait, if visual length is longer, we need LESS padding characters to reach the same width)
    right_pad = width - 2 - len(title_text) - left_pad - visual_offset

    if right_pad < 0:
        right_pad = 0

    return f"{TL_CORNER}{H_LINE * left_pad}{Colors.BOLD}{title_text}{Colors.ENDC}{color}{H_LINE * right_pad}{TR_CORNER}"


def _wrap_content(content: str, width: int) -> list[str]:
    lines = content.split('\n')
    wrapped_lines = []

    for line in lines:
        if not line:
            wrapped_lines.append("")
            continue

        # We need to account for ANSI codes when wrapping, but textwrap doesn't ignore them.
        # A simple approach for now:
        # 1. If line is short, just add it
        # 2. If line is long, wrap it based on visible length

        visible_len = len(strip_ansi(line))
        if visible_len <= width - 4:
            wrapped_lines.append(line)
        else:
            # Simple word wrap
            current_line: list[str] = []
            current_len = 0
            words = line.split(' ')

            for word in words:
                word_len = len(strip_ansi(word))
                if current_len + word_len + 1 > width - 4:
                    wrapped_lines.append(" ".join(current_line))
                    current_line = [word]
                    current_len = word_len
                else:
                    current_line.append(word)
                    current_len += word_len + 1
            if current_line:
                wrapped_lines.append(" ".join(current_line))
    return wrapped_lines


def print_panel(content: str, title: str = "", color: str = Colors.CYAN, width: int = 60) -> None:
    """Prints content inside a bordered panel."""
    # Box drawing characters
    H_LINE = "─"
    V_LINE = "│"
    BL_CORNER = "╰"
    BR_CORNER = "╯"

    top_border = _create_top_border(title, width, color)
    print(f"{color}{top_border}{Colors.ENDC}")

    wrapped_lines = _wrap_content(content, width)

    for line in wrapped_lines:
        visible_len = len(strip_ansi(line))
        padding = width - 4 - visible_len
        if padding < 0:
             padding = 0
        print(f"{color}{V_LINE}{Colors.ENDC} {line}{' ' * padding} {color}{V_LINE}{Colors.ENDC}")

    print(f"{color}{BL_CORNER}{H_LINE * (width - 2)}{BR_CORNER}{Colors.ENDC}")


class Spinner:
    """A simple terminal spinner for long-running operations.

    Displays a spinning animation during execution and updates to a
    success (✔) or failure (✖) state upon completion.
    """

    def __init__(self, message: str = "Processing", success_message: Optional[str] = None):
        self.message = message
        self.success_message = success_message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not self._stop_event.is_set():
            sys.stdout.write(f"\r{Colors.CYAN}{chars[i % len(chars)]}{Colors.ENDC} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def update(self, message: str) -> None:
        """Update the spinner message."""
        # Ensure new message overwrites old one completely if shorter
        padding = max(0, len(self.message) - len(message))
        self.message = message + " " * padding

    def __enter__(self) -> 'Spinner':
        if sys.stdout.isatty():
            sys.stdout.write("\033[?25l")  # Hide cursor
            sys.stdout.flush()
        self._thread.start()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> None:
        self._stop_event.set()
        self._thread.join()

        # Even if not TTY, we want to print the final status if possible,
        # but the current implementation limits it to TTY.
        # We will keep the TTY check for now to avoid breaking non-interactive logs.
        if sys.stdout.isatty():
            sys.stdout.write("\033[?25h")  # Show cursor

            if exc_type:
                symbol = f"{Colors.FAIL}✖{Colors.ENDC}"
            else:
                symbol = f"{Colors.GREEN}✔{Colors.ENDC}"
                if self.success_message:
                    self.message = self.success_message

            # Overwrite the spinner with final status
            # Use ANSI clear line (K) to clear any previous longer message
            sys.stdout.write(f"\r{symbol} {self.message}\033[K\n")
            sys.stdout.flush()


def print_header(title: str, char: str = "=", width: int = 50) -> None:
    """Prints a formatted header."""
    print("")
    print(f"{Colors.BOLD}{Colors.BLUE}{char * width}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{char * width}{Colors.ENDC}")


def print_workflow_report(
    title: str,
    slug: str,
    repo_url: str,
    session_id: Optional[str] = None,
    session_url: Optional[str] = None,
    pr_url: Optional[str] = None
) -> None:
    """Prints a summary report of the workflow results."""
    print_header("✨ WORKFLOW COMPLETE")
    print(f"{Colors.BOLD}📦 Project:{Colors.ENDC} {Colors.GREEN}{title}{Colors.ENDC}")
    print(f"{Colors.BOLD}📝 Slug:   {Colors.ENDC} {slug}")
    print(f"{Colors.BOLD}🔗 Repo:   {Colors.ENDC} {Colors.UNDERLINE}{repo_url}{Colors.ENDC}")
    
    if session_id:
        print(f"{Colors.BOLD}🤖 Jules:  {Colors.ENDC} {Colors.UNDERLINE}{session_url or 'N/A'}{Colors.ENDC}")
        print(f"{Colors.BOLD}   Session:{Colors.ENDC} {session_id}")
        if pr_url:
            print(f"{Colors.BOLD}🎉 PR:     {Colors.ENDC} {Colors.UNDERLINE}{Colors.GREEN}{pr_url}{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}⚠️  Jules session was not created (source not indexed){Colors.ENDC}")
    
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 50}{Colors.ENDC}")


def print_session_status(
    session_id: str,
    title: str,
    url: str,
    is_complete: bool,
    pr_url: Optional[str] = None,
    activities: Optional[list[str]] = None
) -> None:
    """Prints status information for a Jules session."""
    print(f"\n{Colors.BOLD}📋 Session Status:{Colors.ENDC} {Colors.CYAN}{session_id}{Colors.ENDC}")
    print(f"   {Colors.BOLD}Title:   {Colors.ENDC} {title}")
    print(f"   {Colors.BOLD}URL:     {Colors.ENDC} {Colors.UNDERLINE}{url}{Colors.ENDC}")
    status_msg = f"{Colors.GREEN}✅ Yes{Colors.ENDC}" if is_complete else f"{Colors.YELLOW}⏳ In Progress{Colors.ENDC}"
    print(f"   {Colors.BOLD}Complete:{Colors.ENDC} {status_msg}")
    
    if pr_url:
        print(f"   {Colors.BOLD}PR:      {Colors.ENDC} {Colors.UNDERLINE}{Colors.GREEN}{pr_url}{Colors.ENDC}")
    
    if activities:
        print(f"\n   {Colors.BOLD}Recent Activity:{Colors.ENDC}")
        for activity in activities[:3]:
            print(f"   - {activity[:70]}")


def format_duration(seconds: int) -> str:
    """Formats a duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m {remaining_seconds}s"


def print_progress(elapsed: int, message: str) -> None:
    """Prints a progress update."""
    duration = format_duration(elapsed)
    print(f"  {Colors.CYAN}[{duration}]{Colors.ENDC} {message[:60]}...")


def print_watch_complete(elapsed: int, pr_url: Optional[str] = None) -> None:
    """Prints session completion message."""
    duration = format_duration(elapsed)
    print(f"\n{Colors.GREEN}✅ Session completed after {duration}!{Colors.ENDC}")
    if pr_url:
        print(f"{Colors.BOLD}🎉 Pull Request:{Colors.ENDC} {Colors.UNDERLINE}{Colors.GREEN}{pr_url}{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}ℹ️  Session completed but no PR was created.{Colors.ENDC}")


def print_watch_timeout(timeout: int, session_url: str) -> None:
    """Prints timeout message."""
    duration = format_duration(timeout)
    print(f"\n{Colors.YELLOW}⏱️  Timeout reached after {duration}. Session still running.{Colors.ENDC}")
    print(f"   Check status at: {Colors.UNDERLINE}{session_url}{Colors.ENDC}")


def print_sources_list(response: dict[str, Any]) -> None:
    """Prints a formatted list of sources."""
    sources = response.get("sources", [])

    print_header("📚 JULES SOURCES")

    if not sources:
        print(f"\n{Colors.YELLOW}No sources found.{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Tips:{Colors.ENDC}")
        print("  • Connect a GitHub repository to Jules to get started")
        return

    print(f"\nFound {len(sources)} source(s):\n")

    for source in sources:
        name = source.get("name", "Unknown")

        print(f"{Colors.GREEN}• {Colors.BOLD}{name}{Colors.ENDC}")
        print("")


def print_idea_summary(idea_data: dict[str, Any]) -> None:
    """Prints a summary of the generated idea."""

    content_lines = []

    # Description
    content_lines.append(f"{Colors.BOLD}📝 Description:{Colors.ENDC}")
    content_lines.append(idea_data['description'])
    content_lines.append("")

    # Tech Stack
    if idea_data.get('tech_stack'):
        tech = ", ".join(idea_data['tech_stack'])
        content_lines.append(f"{Colors.BOLD}🛠️  Tech Stack:{Colors.ENDC}")
        content_lines.append(tech)
        content_lines.append("")

    # Features
    if idea_data.get('features'):
        content_lines.append(f"{Colors.BOLD}⚡ Features:{Colors.ENDC}")
        for feature in idea_data['features']:
            content_lines.append(f"• {feature}")

    # Remove trailing empty line if exists
    if content_lines and content_lines[-1] == "":
        content_lines.pop()

    full_content = "\n".join(content_lines)

    print("") # spacing before
    print_panel(
        full_content,
        title=f"✨ {idea_data['title']}",
        color=Colors.HEADER,
        width=70
    )
    print("") # spacing after
