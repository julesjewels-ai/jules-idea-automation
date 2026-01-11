"""Command handlers for the CLI."""

import sys
import time
from argparse import Namespace

from src.utils.reporter import (
    print_session_status,
    print_watch_complete,
    print_watch_timeout,
    print_progress,
    print_sources_list,
    print_idea_summary,
    Spinner,
    Colors,
    format_duration,
)


def handle_list_sources() -> None:
    """Handle the list-sources command."""
    from src.services.jules import JulesClient

    client = JulesClient()
    with Spinner("Fetching sources...", success_message="Sources fetched"):
        sources = client.list_sources()

    print_sources_list(sources)


def _execute_and_watch(idea_data: dict, args: Namespace) -> None:
    """Executes workflow and optionally watches session."""
    from src.core.workflow import IdeaWorkflow

    print_idea_summary(idea_data)

    workflow = IdeaWorkflow()
    result = workflow.execute(
        idea_data,
        private=args.private,
        timeout=args.timeout
    )

    if result.session_id and args.watch:
        watch_session(result.session_id, timeout=args.timeout)


def handle_agent(args: Namespace) -> None:
    """Handle the agent command."""
    from src.services.gemini import GeminiClient

    category = getattr(args, 'category', None)

    gemini = GeminiClient()
    msg = f"Generating idea with Gemini{f' (category: {category})' if category else ''}..."
    with Spinner(msg, success_message="Idea generated"):
        idea_data = gemini.generate_idea(category=category)

    _execute_and_watch(idea_data, args)


def handle_website(args: Namespace) -> None:
    """Handle the website command."""
    from src.services.gemini import GeminiClient
    from src.services.scraper import scrape_text, ScrapingError

    print(f"Scraping {args.url}...")
    
    try:
        with Spinner(f"Scraping {args.url}..."):
            text = scrape_text(args.url)
    except ScrapingError as e:
        print(f"\n{Colors.FAIL}❌ Scraping failed: {e}{Colors.ENDC}", file=sys.stderr)
        print(f"\n{Colors.YELLOW}Tips:{Colors.ENDC}", file=sys.stderr)
        print("  • Ensure the URL is publicly accessible (no login required)", file=sys.stderr)
        print("  • Try a different URL that contains the idea description", file=sys.stderr)
        print("  • Use 'python main.py agent' to generate a random idea instead", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ Extracted {len(text)} characters of content")
    
    gemini = GeminiClient()
    with Spinner("Extracting idea with Gemini...", success_message="Idea extracted"):
        idea_data = gemini.extract_idea_from_text(text)
    
    _execute_and_watch(idea_data, args)


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
    """Watch a Jules session until completion or timeout."""
    from src.services.jules import JulesClient
    from src.utils.polling import poll_with_result

    jules = JulesClient()
    
    def get_status() -> str:
        try:
            activities = jules.list_activities(session_id, page_size=1)
            if activities.get("activities"):
                return activities["activities"][0].get("progressUpdated", {}).get("title", "Working...")
            return "Working..."
        except Exception:
            return "Polling..."

    start_time = time.time()

    with Spinner(f"[0s] Watching session {session_id}...") as spinner:
        def update_spinner(elapsed: int, status: str) -> None:
            spinner.update(f"[{format_duration(elapsed)}] {status}")

        is_complete, pr_url = poll_with_result(
            check=lambda: jules.is_session_complete(session_id),
            timeout=timeout,
            interval=30,
            on_poll=update_spinner,
            status_extractor=get_status
        )

    elapsed = int(time.time() - start_time)

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
