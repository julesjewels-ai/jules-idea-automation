"""Command handlers for the CLI."""

from __future__ import annotations

import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

from src.utils.reporter import (
    Spinner,
    format_duration,
    print_demo_report,
    print_idea_summary,
    print_session_status,
    print_sources_list,
    print_watch_complete,
    print_watch_timeout,
)


def _build_gemini_client() -> Any:
    """Create a GeminiClient with the default FileCacheProvider."""
    from src.services.cache import FileCacheProvider
    from src.services.gemini import GeminiClient

    return GeminiClient(cache_provider=FileCacheProvider())


def handle_list_sources() -> None:
    """Handle the list-sources command."""
    from src.services.jules import JulesClient

    client = JulesClient()
    with Spinner("Fetching sources...", success_message="Sources fetched"):
        sources = client.list_sources()

    print_sources_list(sources)


def handle_agent(args: Namespace) -> None:
    """Handle the agent command."""
    category = getattr(args, "category", None)

    gemini = _build_gemini_client()
    msg = f"Generating idea with Gemini{f' (category: {category})' if category else ''}..."
    with Spinner(msg, success_message="Idea generated"):
        idea_data = gemini.generate_idea(category=category)

    _execute_and_watch(args, idea_data, gemini=gemini)


def handle_website(args: Namespace) -> None:
    """Handle the website command."""
    content = getattr(args, "content", None)

    if content:
        # Direct content provided — skip scraping entirely
        text = content
    else:
        from src.services.scraper import scrape_text

        with Spinner(f"Scraping {args.url}...", success_message="Page scraped"):
            text = scrape_text(args.url)

    gemini = _build_gemini_client()
    with Spinner("Extracting idea with Gemini...", success_message="Idea extracted"):
        idea_data = gemini.extract_idea_from_text(text)

    _execute_and_watch(args, idea_data, gemini=gemini)


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
            title=session.get("title", "N/A"),
            url=session.get("url", "N/A"),
            is_complete=is_complete,
            pr_url=pr_url,
            activities=activity_titles,
        )


def _execute_demo(idea_data: dict[str, Any], gemini: Any | None = None) -> None:
    """Run the Gemini-only demo flow (no GitHub/Jules needed)."""
    if gemini is None:
        gemini = _build_gemini_client()

    print_idea_summary(idea_data)

    with Spinner("Generating MVP scaffold preview...", success_message="Scaffold generated"):
        scaffold = gemini.generate_project_scaffold(idea_data)

    feature_maps = None
    try:
        with Spinner("Generating feature maps...", success_message="Feature maps generated"):
            feature_maps = gemini.generate_feature_maps(idea_data, scaffold.get("files", []))
    except Exception:
        pass  # Feature maps are optional in demo

    print_demo_report(idea_data, scaffold, feature_maps)


def _execute_and_watch(args: Namespace, idea_data: dict[str, Any], gemini: Any | None = None) -> None:
    """Execute the workflow and watch the session if requested.

    Args:
    ----
        args: Command line arguments containing public and timeout settings
        idea_data: The idea data to process
        gemini: Optional pre-constructed GeminiClient (avoids re-creation)

    """
    # Demo mode: Gemini-only preview, skip GitHub/Jules entirely
    if getattr(args, "demo", False):
        _execute_demo(idea_data, gemini)
        return

    from src.core.events import WorkflowCompleted, WorkflowStarted
    from src.core.workflow import IdeaWorkflow
    from src.services.audit import JsonFileAuditLogger
    from src.services.bus import LocalEventBus

    print_idea_summary(idea_data)

    if gemini is None:
        gemini = _build_gemini_client()

    event_bus = LocalEventBus()
    audit_logger = JsonFileAuditLogger()
    event_bus.subscribe(WorkflowStarted, audit_logger)
    event_bus.subscribe(WorkflowCompleted, audit_logger)

    workflow = IdeaWorkflow(gemini=gemini, event_bus=event_bus)

    result = workflow.execute(idea_data, private=not args.public, timeout=args.timeout)

    if result.session_id and args.watch:
        watch_session(result.session_id, timeout=args.timeout)


def watch_session(session_id: str, timeout: int = 1800) -> tuple[bool, str | None]:
    """Watch a Jules session until completion or timeout.

    Args:
    ----
        session_id: The session ID to watch
        timeout: Max seconds to wait

    Returns:
    -------
        Tuple of (is_complete, pr_url or None)

    """
    from src.services.jules import JulesClient
    from src.utils.polling import poll_with_result

    jules = JulesClient()
    poll_interval = 30

    with Spinner(f"[{format_duration(0)}] Watching session {session_id}...") as spinner:

        def check() -> tuple[bool, str | None]:
            return jules.is_session_complete(session_id)

        def status_extractor() -> str:
            try:
                activities = jules.list_activities(session_id, page_size=1)
                if activities.get("activities"):
                    latest = activities["activities"][0]
                    return str(latest.get("progressUpdated", {}).get("title", "Working..."))
                return "Working..."
            except Exception:
                return "Polling..."

        def on_poll(elapsed: int, status: str) -> None:
            spinner.update(f"[{format_duration(elapsed)}] {status}")

        is_complete, pr_url, elapsed = poll_with_result(
            check=check,
            timeout=timeout,
            interval=poll_interval,
            on_poll=on_poll,
            status_extractor=status_extractor,
        )

    if is_complete:
        print_watch_complete(elapsed, pr_url)
        return is_complete, pr_url

    session = jules.get_session(session_id)
    print_watch_timeout(timeout, session.get("url", "N/A"))
    return False, None


def handle_guide(args: Namespace) -> None:
    """Handle the guide command."""
    from src.utils.guide import (
        print_agent_guide,
        print_examples,
        print_manual_guide,
        print_website_guide,
        print_welcome_guide,
    )

    workflow = getattr(args, "workflow", None)

    guides = {
        "agent": print_agent_guide,
        "website": print_website_guide,
        "manual": print_manual_guide,
    }

    guide_fn = guides.get(workflow) if workflow else None
    if guide_fn:
        guide_fn()
    else:
        print_welcome_guide()
        print_examples()


def _parse_title_and_description(args: Namespace) -> tuple[str, str]:
    """Parse title and description from arguments.

    Handles the case where a long title is provided
    (Description-as-Title pattern).
    """
    raw_title = args.title

    if len(raw_title) > 100:
        # If the title is too long, it's likely a full description
        description = raw_title
        # Use first sentence or prefix as a title
        title = raw_title[:50].split(".")[0].strip() or "Manual Idea"
    else:
        title = raw_title
        description = args.description or raw_title

    return title, description


def _parse_list_arg(arg_value: str | None) -> list[str]:
    """Parse a comma-separated list argument."""
    if not arg_value:
        return []
    return [item.strip() for item in arg_value.split(",")]


def handle_manual(args: Namespace) -> None:
    """Handle the manual command."""
    from src.utils.slugify import slugify

    title, description = _parse_title_and_description(args)

    # Generate slug from title if not provided
    slug = args.slug or slugify(title)

    # Construct idea_data dictionary compatible with IdeaResponse
    idea_data = {
        "title": title,
        "description": description,
        "slug": slug,
        "tech_stack": _parse_list_arg(args.tech_stack),
        "features": _parse_list_arg(args.features),
    }

    _execute_and_watch(args, idea_data)


def _read_clipboard() -> str:
    """Read content from the system clipboard using pbpaste (macOS).

    Returns
    -------
        Clipboard text content

    Raises
    ------
        RuntimeError: If clipboard cannot be read

    """
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pbpaste failed: {result.stderr.strip()}")
        return result.stdout
    except FileNotFoundError:
        raise RuntimeError(
            "Clipboard reading requires 'pbpaste' (macOS only). On other systems, use --file or pipe via stdin instead."
        )


def _read_paste_content(args: Namespace) -> str:
    """Determine the content source for the paste command and read it.

    Priority: --clipboard > --file > stdin pipe (-) > interactive input.

    Returns
    -------
        The text content to process

    Raises
    ------
        SystemExit: If content is insufficient

    """
    from src.services.scraper import MIN_CONTENT_LENGTH

    text = ""

    if getattr(args, "clipboard", False):
        text = _read_clipboard()
    elif getattr(args, "file_path", None):
        path = Path(args.file_path)
        if not path.exists():
            print(f"Error: File not found: {args.file_path}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
    elif getattr(args, "content_source", None) == "-":
        # Read from stdin pipe
        text = sys.stdin.read()
    else:
        # Interactive mode — prompt user to paste
        print("Paste your content below, then type END on its own line to submit:")
        print("─" * 60)
        lines: list[str] = []
        try:
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
        except EOFError:
            pass  # Ctrl-D also works
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)
        text = "\n".join(lines)

    text = text.strip()

    if len(text) < MIN_CONTENT_LENGTH:
        print(
            f"Error: Content too short ({len(text)} chars, minimum {MIN_CONTENT_LENGTH}). "
            "Please provide more content for idea extraction.",
            file=sys.stderr,
        )
        sys.exit(1)

    return text


def handle_paste(args: Namespace) -> None:
    """Handle the paste command — direct content input for idea extraction."""
    # Determine source label for UX feedback
    if getattr(args, "clipboard", False):
        source_label = "📋 clipboard"
    elif getattr(args, "file_path", None):
        source_label = f"📄 {args.file_path}"
    elif getattr(args, "content_source", None) == "-":
        source_label = "⎔ stdin"
    else:
        source_label = "⌨️  interactive"

    text = _read_paste_content(args)

    # Show content preview so user knows what was captured
    preview = text[:200].replace("\n", " ")
    if len(text) > 200:
        preview += "..."
    print(f"\n✔ Read {len(text):,} chars from {source_label}")
    print(f"  Preview: {preview}\n")

    gemini = _build_gemini_client()
    with Spinner("Extracting idea with Gemini...", success_message="Idea extracted"):
        idea_data = gemini.extract_idea_from_text(text)

    _execute_and_watch(args, idea_data, gemini=gemini)


def dispatch_command(args: Namespace) -> None:
    """Dispatch to the appropriate command handler."""
    handlers = {
        "list-sources": lambda: handle_list_sources(),
        "agent": lambda: handle_agent(args),
        "website": lambda: handle_website(args),
        "paste": lambda: handle_paste(args),
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
