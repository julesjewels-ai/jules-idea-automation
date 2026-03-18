"""CLI argument parser for Jules Automation Tool."""

from __future__ import annotations

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Creates and configures the argument parser."""
    parser = argparse.ArgumentParser(description="Jules Automation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list-sources
    subparsers.add_parser("list-sources", help="List available Jules sources")

    # Command: agent
    agent_parser = subparsers.add_parser("agent", help="Generate an idea using Gemini and send to Jules")
    agent_parser.add_argument(
        "--category",
        choices=["web_app", "cli_tool", "api_service", "mobile_app", "automation", "ai_ml"],
        help="Target a specific category for idea generation",
    )
    agent_parser.add_argument("--public", action="store_true", help="Create a public repository (default: private)")
    agent_parser.add_argument(
        "--timeout", type=int, default=1800, help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    agent_parser.add_argument("--watch", action="store_true", help="Watch the session until completion and show PR URL")

    # Command: website
    website_parser = subparsers.add_parser("website", help="Scrape a website for an idea and send to Jules")
    website_input = website_parser.add_mutually_exclusive_group(required=True)
    website_input.add_argument("--url", help="URL to scrape")
    website_input.add_argument("--content", help="Page content to use directly (bypasses scraping)")
    website_parser.add_argument("--public", action="store_true", help="Create a public repository (default: private)")
    website_parser.add_argument(
        "--timeout", type=int, default=1800, help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    website_parser.add_argument(
        "--watch", action="store_true", help="Watch the session until completion and show PR URL"
    )

    # Command: paste
    paste_parser = subparsers.add_parser(
        "paste", help="Paste or pipe content directly for idea extraction (bypasses web scraping)"
    )
    paste_parser.add_argument(
        "content_source",
        nargs="?",
        default=None,
        help="Use '-' to read from stdin pipe",
    )
    paste_parser.add_argument("--file", dest="file_path", help="Read content from a file")
    paste_parser.add_argument(
        "--clipboard", action="store_true", help="Read content from the system clipboard (macOS pbpaste)"
    )
    paste_parser.add_argument("--public", action="store_true", help="Create a public repository (default: private)")
    paste_parser.add_argument(
        "--timeout", type=int, default=1800, help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    paste_parser.add_argument(
        "--watch", action="store_true", help="Watch the session until completion and show PR URL"
    )

    # Command: status
    status_parser = subparsers.add_parser("status", help="Check status of a Jules session")
    status_parser.add_argument("session_id", help="The session ID to check")
    status_parser.add_argument("--watch", action="store_true", help="Watch the session until completion")
    status_parser.add_argument(
        "--timeout", type=int, default=1800, help="Timeout in seconds for watching (default: 1800 = 30 min)"
    )

    # Command: guide
    guide_parser = subparsers.add_parser("guide", help="Show interactive user guide with workflow examples")
    guide_parser.add_argument(
        "--workflow", choices=["agent", "website", "manual"], help="Show detailed guide for a specific workflow"
    )

    # Command: manual
    manual_parser = subparsers.add_parser("manual", help="Provide your own custom idea and details")
    manual_parser.add_argument("title", help="Project title (used to generate slug if --slug not provided)")
    manual_parser.add_argument("--description", help="Detailed project description (defaults to title if omitted)")
    manual_parser.add_argument("--slug", help="Custom GitHub repository slug (auto-generated from title if omitted)")
    manual_parser.add_argument(
        "--tech_stack", help="Comma-separated list of technologies (e.g., 'Python,Flask,PostgreSQL')"
    )
    manual_parser.add_argument("--features", help="Comma-separated list of key features (e.g., 'Auth,CRUD,Export')")
    manual_parser.add_argument("--public", action="store_true", help="Create a public repository (default: private)")
    manual_parser.add_argument(
        "--timeout", type=int, default=1800, help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    manual_parser.add_argument(
        "--watch", action="store_true", help="Watch the session until completion and show PR URL"
    )

    return parser
