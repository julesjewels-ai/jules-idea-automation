"""Command handlers for the CLI."""

import sys
from argparse import Namespace

from src.utils.reporter import (
    print_session_status,
    print_watch_complete,
    print_watch_timeout,
    print_sources_list,
    print_idea_summary,
    Spinner,
    format_duration,
)


def handle_list_sources() -> None:
    """Handle the list-sources command."""
    from src.services.jules import JulesClient

    client = JulesClient()
    with Spinner("Fetching sources...", success_message="Sources fetched"):
        sources = client.list_sources()

    print_sources_list(sources)


def handle_agent(args: Namespace) -> None:
    """Handle the agent command."""
    from src.services.gemini import GeminiClient

    category = getattr(args, 'category', None)

    gemini = GeminiClient()
    msg = f"Generating idea with Gemini{f' (category: {category})' if category else ''}..."
    with Spinner(msg, success_message="Idea generated"):
        idea_data = gemini.generate_idea(category=category)

    _execute_and_watch(args, idea_data)


def handle_website(args: Namespace) -> None:
    """Handle the website command."""
    from src.services.gemini import GeminiClient
    from src.services.scraper import scrape_text

    print(f"Scraping {args.url}...")

    with Spinner(f"Scraping {args.url}..."):
        text = scrape_text(args.url)

    print(f"✓ Extracted {len(text)} characters of content")

    gemini = GeminiClient()
    with Spinner("Extracting idea with Gemini...", success_message="Idea extracted"):
        idea_data = gemini.extract_idea_from_text(text)

    _execute_and_watch(args, idea_data)


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


def _execute_and_watch(args: Namespace, idea_data: dict) -> None:
    """Execute the workflow and watch the session if requested.

    Args:
        args: Command line arguments containing private and timeout settings
        idea_data: The idea data to process
    """
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


def watch_session(session_id: str, timeout: int = 1800) -> tuple:
    """Watch a Jules session until completion or timeout.

    Args:
        session_id: The session ID to watch
        timeout: Max seconds to wait

    Returns:
        Tuple of (is_complete, pr_url or None)
    """
    from src.services.jules import JulesClient
    from src.utils.polling import poll_with_result

    jules = JulesClient()
    poll_interval = 30

    with Spinner(f"[{format_duration(0)}] Watching session {session_id}...") as spinner:

        def check():
            return jules.is_session_complete(session_id)

        def status_extractor():
            try:
                activities = jules.list_activities(session_id, page_size=1)
                if activities.get("activities"):
                    latest = activities["activities"][0]
                    return latest.get("progressUpdated", {}).get("title", "Working...")
                return "Working..."
            except Exception:
                return "Polling..."

        def on_poll(elapsed, status):
            spinner.update(f"[{format_duration(elapsed)}] {status}")

        is_complete, pr_url, elapsed = poll_with_result(
            check=check,
            timeout=timeout,
            interval=poll_interval,
            on_poll=on_poll,
            status_extractor=status_extractor
        )

    if is_complete:
        print_watch_complete(elapsed, pr_url)
        return is_complete, pr_url

    session = jules.get_session(session_id)
    print_watch_timeout(timeout, session.get('url', 'N/A'))
    return False, None


def handle_guide(args: Namespace) -> None:
    """Handle the guide command."""
    from src.utils.guide import (
        print_welcome_guide,
        print_agent_guide,
        print_website_guide,
        print_manual_guide,
        print_examples
    )

    workflow = getattr(args, 'workflow', None)

    if workflow == 'agent':
        print_agent_guide()
    elif workflow == 'website':
        print_website_guide()
    elif workflow == 'manual':
        print_manual_guide()
    else:
        # Show welcome guide with all options
        print_welcome_guide()
        print_examples()


def handle_manual(args: Namespace) -> None:
    """Handle the manual command."""
    from src.utils.slugify import slugify

    raw_title = args.title

    # Handle very long titles gracefully (Description-as-Title pattern)
    if len(raw_title) > 100:
        # If the title is too long, it's likely a full description
        description = raw_title
        # Use first sentence or prefix as a title
        title = raw_title[:50].split('.')[0].strip() or "Manual Idea"
    else:
        title = raw_title
        description = args.description or raw_title

    # Generate slug from title if not provided
    slug = args.slug or slugify(title)

    # Parse comma-separated lists
    tech_stack = []
    if args.tech_stack:
        tech_stack = [item.strip() for item in args.tech_stack.split(',')]

    features = []
    if args.features:
        features = [item.strip() for item in args.features.split(',')]

    # Construct idea_data dictionary compatible with IdeaResponse
    idea_data = {
        "title": title,
        "description": description,
        "slug": slug,
        "tech_stack": tech_stack,
        "features": features
    }

    _execute_and_watch(args, idea_data)


def dispatch_command(args: Namespace) -> None:
    """Dispatch to the appropriate command handler."""
    handlers = {
        "list-sources": lambda: handle_list_sources(),
        "agent": lambda: handle_agent(args),
        "website": lambda: handle_website(args),
        "status": lambda: handle_status(args),
        "guide": lambda: handle_guide(args),
        "manual": lambda: handle_manual(args),
    }

    handler = handlers.get(args.command)
    if handler:
        handler()
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)
