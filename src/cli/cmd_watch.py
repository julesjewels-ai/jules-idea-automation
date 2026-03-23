"""Handler for session watching and the 'status' command."""

from __future__ import annotations

from argparse import Namespace

from src.utils.reporter import (
    Spinner,
    format_duration,
    print_session_status,
    print_sources_list,
    print_watch_complete,
    print_watch_timeout,
)


def handle_list_sources() -> None:
    """Handle the list-sources command."""
    from src.services.jules import JulesClient

    client = JulesClient()
    with Spinner("Fetching sources...", success_message="Sources fetched"):
        sources = client.list_sources()

    print_sources_list(sources)


def handle_status(args: Namespace) -> None:
    """Handle the status command."""
    from src.services.jules import JulesClient

    client = JulesClient()
    session_id = args.session_id

    if args.watch:
        watch_session(session_id, timeout=args.timeout)
    else:
        with Spinner("Fetching session status…", success_message="Status fetched"):
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
