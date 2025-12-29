"""Command handlers for the CLI."""

import json
import sys
import time
from argparse import Namespace

from src.utils.reporter import (
    print_session_status,
    print_watch_complete,
    print_watch_timeout,
    print_progress,
    Spinner
)


def handle_list_sources() -> None:
    """Handle the list-sources command."""
    from src.services.jules import JulesClient

    client = JulesClient()
    sources = client.list_sources()
    print(json.dumps(sources, indent=2))


def handle_agent(args: Namespace) -> None:
    """Handle the agent command."""
    from src.services.gemini import GeminiClient
    from src.core.workflow import IdeaWorkflow

    category = getattr(args, 'category', None)
    
    gemini = GeminiClient()
    msg = f"Generating idea with Gemini{f' (category: {category})' if category else ''}..."
    with Spinner(msg):
        idea_data = gemini.generate_idea(category=category)
    
    workflow = IdeaWorkflow()
    result = workflow.execute(
        idea_data,
        private=args.private,
        timeout=args.timeout
    )
    
    if result.session_id and args.watch:
        watch_session(result.session_id, timeout=args.timeout)


def handle_website(args: Namespace) -> None:
    """Handle the website command."""
    from src.services.gemini import GeminiClient
    from src.services.scraper import scrape_text, ScrapingError
    from src.core.workflow import IdeaWorkflow

    print(f"Scraping {args.url}...")
    
    try:
        with Spinner(f"Scraping {args.url}..."):
            text = scrape_text(args.url)
    except ScrapingError as e:
        print(f"\n❌ Scraping failed: {e}", file=sys.stderr)
        print("\nTips:", file=sys.stderr)
        print("  • Ensure the URL is publicly accessible (no login required)", file=sys.stderr)
        print("  • Try a different URL that contains the idea description", file=sys.stderr)
        print("  • Use 'python main.py agent' to generate a random idea instead", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ Extracted {len(text)} characters of content")
    
    gemini = GeminiClient()
    with Spinner("Extracting idea with Gemini..."):
        idea_data = gemini.extract_idea_from_text(text)
    
    workflow = IdeaWorkflow()
    result = workflow.execute(
        idea_data,
        private=args.private,
        timeout=args.timeout
    )
    
    if result.session_id and args.watch:
        watch_session(result.session_id, timeout=args.timeout)


def handle_status(args: Namespace) -> None:
    """Handle the status command."""
    from src.services.jules import JulesClient

    client = JulesClient()
    session_id = args.session_id
    
    if args.watch:
        watch_session(session_id, timeout=args.timeout)
    else:
        session = client.get_session(session_id)
        is_complete, pr_url = client.is_session_complete(session_id)
        
        # Get recent activity titles
        activities = client.list_activities(session_id, page_size=3)
        activity_titles = []
        for act in activities.get("activities", []):
            title = act.get("progressUpdated", {}).get("title", "")
            if title:
                activity_titles.append(title)
        
        print_session_status(
            session_id=session_id,
            title=session.get('title', 'N/A'),
            url=session.get('url', 'N/A'),
            is_complete=is_complete,
            pr_url=pr_url,
            activities=activity_titles
        )


def watch_session(session_id: str, timeout: int = 1800) -> tuple:
    """Watch a Jules session until completion or timeout.
    
    Args:
        session_id: The session ID to watch
        timeout: Max seconds to wait
    
    Returns:
        Tuple of (is_complete, pr_url or None)
    """
    from src.services.jules import JulesClient

    jules = JulesClient()
    poll_interval = 30
    elapsed = 0
    is_complete = False
    pr_url = None
    
    with Spinner(f"[{elapsed}s] Watching session {session_id}...") as spinner:
        while elapsed < timeout:
            is_complete, pr_url = jules.is_session_complete(session_id)

            if is_complete:
                break

            # Show latest activity
            try:
                activities = jules.list_activities(session_id, page_size=1)
                if activities.get("activities"):
                    latest = activities["activities"][0]
                    title = latest.get("progressUpdated", {}).get("title", "Working...")
                    spinner.update(f"[{elapsed}s] {title}")
                else:
                    spinner.update(f"[{elapsed}s] Working...")
            except Exception:
                spinner.update(f"[{elapsed}s] Polling...")

            time.sleep(poll_interval)
            elapsed += poll_interval
    
    if is_complete:
        print_watch_complete(elapsed, pr_url)
        return is_complete, pr_url

    session = jules.get_session(session_id)
    print_watch_timeout(timeout, session.get('url', 'N/A'))
    return False, None


def dispatch_command(args: Namespace) -> None:
    """Dispatch to the appropriate command handler."""
    handlers = {
        "list-sources": lambda: handle_list_sources(),
        "agent": lambda: handle_agent(args),
        "website": lambda: handle_website(args),
        "status": lambda: handle_status(args),
    }
    
    handler = handlers.get(args.command)
    if handler:
        handler()
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)
