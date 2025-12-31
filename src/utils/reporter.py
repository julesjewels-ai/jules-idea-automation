"""Console reporting utilities."""

import sys
import time
import threading
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


class Spinner:
    """A simple terminal spinner for long-running operations."""

    def __init__(self, message: str = "Processing"):
        self.message = message
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
        # Clear line on exit
        sys.stdout.write(f"\r{' ' * (len(self.message) + 10)}\r")
        sys.stdout.flush()

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
        if sys.stdout.isatty():
            sys.stdout.write("\033[?25h")  # Show cursor
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
