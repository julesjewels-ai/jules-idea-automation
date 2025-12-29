"""CLI argument parser for Jules Automation Tool."""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Creates and configures the argument parser."""
    parser = argparse.ArgumentParser(description="Jules Automation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list-sources
    subparsers.add_parser("list-sources", help="List available Jules sources")

    # Command: agent
    agent_parser = subparsers.add_parser(
        "agent", 
        help="Generate an idea using Gemini and send to Jules"
    )
    agent_parser.add_argument(
        "--category", 
        choices=["web_app", "cli_tool", "api_service", "mobile_app", "automation", "ai_ml"],
        help="Target a specific category for idea generation"
    )
    agent_parser.add_argument(
        "--private",
        action="store_true",
        help="Create a private repository (default: public)"
    )
    agent_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    agent_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the session until completion and show PR URL"
    )

    # Command: website
    website_parser = subparsers.add_parser(
        "website", 
        help="Scrape a website for an idea and send to Jules"
    )
    website_parser.add_argument("--url", required=True, help="URL to scrape")
    website_parser.add_argument(
        "--private",
        action="store_true",
        help="Create a private repository (default: public)"
    )
    website_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    website_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the session until completion and show PR URL"
    )

    # Command: status
    status_parser = subparsers.add_parser(
        "status", 
        help="Check status of a Jules session"
    )
    status_parser.add_argument("session_id", help="The session ID to check")
    status_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the session until completion"
    )
    status_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for watching (default: 1800 = 30 min)"
    )

    return parser
