"""Console reporting utilities."""

import sys
import time
import threading
import re
from typing import Optional


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


def print_panel(lines: list[str], title: str = "", width: int = 60, border_color: str = Colors.BLUE) -> None:
    """Prints a message in a box."""
    # Calculate width based on longest line if it exceeds default
    # Add 4 for padding (2 spaces left, 2 spaces right)
    max_content_len = max([len(strip_ansi(line)) for line in lines] + [len(title) + 4]) if lines else 0
    width = max(width, max_content_len + 4)

    # borders
    tl, tr, bl, br = "╭", "╮", "╰", "╯"
    h, v = "─", "│"

    # Title handling
    if title:
        title_text = f" {title} "
        # Title is bold header color
        # We need to calculate title length without colors just in case (though here it's plain string)
        title_len = len(title_text)
        right_dash_len = width - 2 - 2 - title_len # -2 for corners, -2 for side dashes if we wanted them centered?
        # Actually standard style: ╭─ Title ──────╮
        right_dash_len = width - 2 - title_len - 1 # -2 corners, -1 left dash

        top_border = f"{tl}{h}{Colors.BOLD}{Colors.HEADER}{title_text}{Colors.ENDC}{border_color}{h * right_dash_len}{tr}"
    else:
        top_border = f"{tl}{h * (width - 2)}{tr}"

    print(f"\n{border_color}{top_border}{Colors.ENDC}")

    for line in lines:
        visible_len = len(strip_ansi(line))
        padding = width - 4 - visible_len
        print(f"{border_color}{v}{Colors.ENDC} {line}{' ' * padding} {border_color}{v}{Colors.ENDC}")

    print(f"{border_color}{bl}{h * (width - 2)}{br}{Colors.ENDC}\n")


class Spinner:
    """A simple terminal spinner for long-running operations.

    Displays a spinning animation during execution and updates to a
    success (✔) or failure (✖) state upon completion.
    """

    def __init__(self, message: str = "Processing", success_message: str = None):
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

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
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
    # Kept for backward compatibility if needed, but preferably use print_panel
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
    lines = []

    lines.append(f"{Colors.BOLD}📦 Project:{Colors.ENDC} {Colors.GREEN}{title}{Colors.ENDC}")
    lines.append(f"{Colors.BOLD}📝 Slug:   {Colors.ENDC} {slug}")
    lines.append(f"{Colors.BOLD}🔗 Repo:   {Colors.ENDC} {Colors.UNDERLINE}{repo_url}{Colors.ENDC}")
    lines.append("") # Empty line for spacing
    
    if session_id:
        lines.append(f"{Colors.BOLD}🤖 Jules:  {Colors.ENDC} {Colors.UNDERLINE}{session_url or 'N/A'}{Colors.ENDC}")
        lines.append(f"{Colors.BOLD}   Session:{Colors.ENDC} {session_id}")
        if pr_url:
             lines.append(f"{Colors.BOLD}🎉 PR:     {Colors.ENDC} {Colors.UNDERLINE}{Colors.GREEN}{pr_url}{Colors.ENDC}")
    else:
        lines.append(f"{Colors.YELLOW}⚠️  Jules session was not created (source not indexed){Colors.ENDC}")

    print_panel(lines, title="✨ WORKFLOW COMPLETE")


def print_session_status(
    session_id: str,
    title: str,
    url: str,
    is_complete: bool,
    pr_url: Optional[str] = None,
    activities: Optional[list[str]] = None
) -> None:
    """Prints status information for a Jules session."""
    lines = []
    lines.append(f"{Colors.BOLD}Title:   {Colors.ENDC} {title}")
    lines.append(f"{Colors.BOLD}URL:     {Colors.ENDC} {Colors.UNDERLINE}{url}{Colors.ENDC}")

    status_msg = f"{Colors.GREEN}✅ Yes{Colors.ENDC}" if is_complete else f"{Colors.YELLOW}⏳ In Progress{Colors.ENDC}"
    lines.append(f"{Colors.BOLD}Complete:{Colors.ENDC} {status_msg}")
    
    if pr_url:
        lines.append(f"{Colors.BOLD}PR:      {Colors.ENDC} {Colors.UNDERLINE}{Colors.GREEN}{pr_url}{Colors.ENDC}")
    
    if activities:
        lines.append("")
        lines.append(f"{Colors.BOLD}Recent Activity:{Colors.ENDC}")
        for activity in activities[:3]:
            # Truncate if too long to fit comfortably in default panel
            act_text = activity if len(activity) < 65 else activity[:62] + "..."
            lines.append(f" - {act_text}")

    print_panel(lines, title=f"📋 Session Status: {session_id}")


def print_progress(elapsed: int, message: str) -> None:
    """Prints a progress update."""
    print(f"  {Colors.CYAN}[{elapsed}s]{Colors.ENDC} {message[:60]}...")


def print_watch_complete(elapsed: int, pr_url: Optional[str] = None) -> None:
    """Prints session completion message."""
    print(f"\n{Colors.GREEN}✅ Session completed after {elapsed}s!{Colors.ENDC}")
    if pr_url:
        print(f"{Colors.BOLD}🎉 Pull Request:{Colors.ENDC} {Colors.UNDERLINE}{Colors.GREEN}{pr_url}{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}ℹ️  Session completed but no PR was created.{Colors.ENDC}")


def print_watch_timeout(timeout: int, session_url: str) -> None:
    """Prints timeout message."""
    print(f"\n{Colors.YELLOW}⏱️  Timeout reached after {timeout}s. Session still running.{Colors.ENDC}")
    print(f"   Check status at: {Colors.UNDERLINE}{session_url}{Colors.ENDC}")

def print_sources_list(response: dict) -> None:
    """Prints a formatted list of sources."""
    sources = response.get("sources", [])

    if not sources:
        print(f"\n{Colors.YELLOW}No sources found.{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Tips:{Colors.ENDC}")
        print("  • Connect a GitHub repository to Jules to get started")
        return

    lines = []
    lines.append(f"Found {len(sources)} source(s):")
    lines.append("")

    for source in sources:
        name = source.get("name", "Unknown")
        lines.append(f"{Colors.GREEN}• {Colors.BOLD}{name}{Colors.ENDC}")

    print_panel(lines, title="📚 JULES SOURCES")


def print_idea_summary(idea_data: dict) -> None:
    """Prints a summary of the generated idea."""
    lines = []
    lines.append(f"{Colors.BOLD}📝 Description:{Colors.ENDC} {idea_data['description']}")

    if idea_data.get('tech_stack'):
        tech = ", ".join(idea_data['tech_stack'])
        lines.append(f"{Colors.BOLD}🛠️  Tech Stack:{Colors.ENDC}  {tech}")

    if idea_data.get('features'):
        lines.append("")
        lines.append(f"{Colors.BOLD}⚡ Features:{Colors.ENDC}")
        for feature in idea_data['features']:
            lines.append(f"   • {feature}")

    print_panel(lines, title=f"✨ Generated Idea: {idea_data['title']}")
