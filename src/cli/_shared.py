"""Shared helpers for CLI command handlers."""

from __future__ import annotations

from argparse import Namespace
from typing import Any

from src.utils.reporter import (
    Spinner,
    print_demo_report,
    print_idea_summary,
)


def build_gemini_client() -> Any:
    """Create a GeminiClient with the default FileCacheProvider."""
    from src.services.cache import FileCacheProvider
    from src.services.gemini import GeminiClient

    return GeminiClient(cache_provider=FileCacheProvider())


def execute_demo(idea_data: dict[str, Any], gemini: Any | None = None) -> None:
    """Run the Gemini-only demo flow (no GitHub/Jules needed)."""
    if gemini is None:
        gemini = build_gemini_client()

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


def execute_and_watch(args: Namespace, idea_data: dict[str, Any], gemini: Any | None = None) -> None:
    """Execute the workflow and watch the session if requested.

    Args:
    ----
        args: Command line arguments containing public and timeout settings
        idea_data: The idea data to process
        gemini: Optional pre-constructed GeminiClient (avoids re-creation)

    """
    # Demo mode: Gemini-only preview, skip GitHub/Jules entirely
    if getattr(args, "demo", False):
        execute_demo(idea_data, gemini)
        return

    from src.core.events import WorkflowCompleted, WorkflowStarted
    from src.core.workflow import IdeaWorkflow
    from src.services.audit import JsonFileAuditLogger
    from src.services.bus import LocalEventBus
    from src.utils.config import preflight_check_credentials

    # Verify GitHub/Jules tokens are valid before spending Gemini credits
    with Spinner("Verifying API credentials…", success_message="Credentials verified"):
        preflight_check_credentials()

    print_idea_summary(idea_data)

    if gemini is None:
        gemini = build_gemini_client()

    event_bus = LocalEventBus()
    audit_logger = JsonFileAuditLogger()
    event_bus.subscribe(WorkflowStarted, audit_logger)
    event_bus.subscribe(WorkflowCompleted, audit_logger)

    workflow = IdeaWorkflow(gemini=gemini, event_bus=event_bus)

    result = workflow.execute(idea_data, private=not args.public, timeout=args.timeout)

    if result.session_id and args.watch:
        from src.cli.cmd_watch import watch_session

        watch_session(result.session_id, timeout=args.timeout)
