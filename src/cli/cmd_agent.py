"""Handler for the 'agent' command."""

from __future__ import annotations

from argparse import Namespace

from src.cli._shared import build_gemini_client, execute_and_watch
from src.utils.reporter import Spinner


def handle_agent(args: Namespace) -> None:
    """Handle the agent command."""
    category = getattr(args, "category", None)

    gemini = build_gemini_client()
    msg = f"Generating idea with Gemini{f' (category: {category})' if category else ''}..."
    with Spinner(msg, success_message="Idea generated"):
        idea_data = gemini.generate_idea(category=category)

    execute_and_watch(args, idea_data, gemini=gemini)
