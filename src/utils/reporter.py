"""Console reporting utilities."""

from typing import Optional


def print_header(title: str, char: str = "=", width: int = 50) -> None:
    """Prints a formatted header."""
    print("")
    print(char * width)
    print(title)
    print(char * width)


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
    print(f"📦 Project: {title}")
    print(f"📝 Slug:    {slug}")
    print(f"🔗 Repo:    {repo_url}")
    
    if session_id:
        print(f"🤖 Jules:   {session_url or 'N/A'}")
        print(f"   Session: {session_id}")
        if pr_url:
            print(f"🎉 PR:      {pr_url}")
    else:
        print("⚠️  Jules session was not created (source not indexed)")
    
    print("=" * 50)


def print_session_status(
    session_id: str,
    title: str,
    url: str,
    is_complete: bool,
    pr_url: Optional[str] = None,
    activities: Optional[list[str]] = None
) -> None:
    """Prints status information for a Jules session."""
    print(f"\n📋 Session Status: {session_id}")
    print(f"   Title:    {title}")
    print(f"   URL:      {url}")
    print(f"   Complete: {'✅ Yes' if is_complete else '⏳ In Progress'}")
    
    if pr_url:
        print(f"   PR:       {pr_url}")
    
    if activities:
        print("\n   Recent Activity:")
        for activity in activities[:3]:
            print(f"   - {activity[:70]}")


def print_progress(elapsed: int, message: str) -> None:
    """Prints a progress update."""
    print(f"  [{elapsed}s] {message[:60]}...")


def print_watch_complete(elapsed: int, pr_url: Optional[str] = None) -> None:
    """Prints session completion message."""
    print(f"\n✅ Session completed after {elapsed}s!")
    if pr_url:
        print(f"🎉 Pull Request: {pr_url}")
    else:
        print("ℹ️  Session completed but no PR was created.")


def print_watch_timeout(timeout: int, session_url: str) -> None:
    """Prints timeout message."""
    print(f"\n⏱️  Timeout reached after {timeout}s. Session still running.")
    print(f"   Check status at: {session_url}")
