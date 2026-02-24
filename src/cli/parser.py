"""Command-line argument parser."""

import argparse
from typing import Any


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        The configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Jules Idea Automation CLI - "
                    "Generate, Scaffold, and Start Jules Sessions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Agent Mode: Generate idea using Gemini
  python main.py agent --category cli_tool --watch

  # Website Mode: Extract idea from URL
  python main.py website --url https://example.com/project-idea

  # Manual Mode: Provide idea details directly
  python main.py manual "My Awesome Tool" --description "A tool that does X"

  # List available Jules sources
  python main.py list-sources
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list-sources
    subparsers.add_parser(
        "list-sources",
        help="List available sources connected to Jules"
    )

    # Command: agent
    agent_parser = subparsers.add_parser(
        "agent",
        help="Generate an idea using an AI agent"
    )
    agent_parser.add_argument(
        "--category",
        choices=[
            "web_app", "cli_tool", "api_service",
            "mobile_app", "automation", "ai_ml"
        ],
        help="Target a specific idea category"
    )
    _add_common_args(agent_parser)

    # Command: website
    website_parser = subparsers.add_parser(
        "website",
        help="Extract an idea from a website URL"
    )
    website_parser.add_argument(
        "--url",
        required=True,
        help="The URL to scrape for the idea"
    )
    _add_common_args(website_parser)

    # Command: manual
    manual_parser = subparsers.add_parser(
        "manual",
        help="Manually provide idea details"
    )
    manual_parser.add_argument(
        "title",
        help="Project title (or full description if very long)"
    )
    manual_parser.add_argument(
        "--description",
        help="Project description (optional if title covers it)"
    )
    manual_parser.add_argument(
        "--slug",
        help="Repository name (slug)"
    )
    manual_parser.add_argument(
        "--tech-stack",
        dest="tech_stack",
        help="Comma-separated list of technologies"
    )
    manual_parser.add_argument(
        "--features",
        help="Comma-separated list of key features"
    )
    _add_common_args(manual_parser)

    # Command: status
    status_parser = subparsers.add_parser(
        "status",
        help="Check the status of a Jules session"
    )
    status_parser.add_argument(
        "session_id",
        help="The ID of the session to check"
    )
    status_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the session status until completion"
    )
    status_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for watch mode (default: 1800)"
    )

    # Command: guide
    guide_parser = subparsers.add_parser(
        "guide",
        help="Show interactive guide and examples"
    )
    guide_parser.add_argument(
        "--workflow",
        choices=["agent", "website", "manual"],
        help="Show guide for specific workflow"
    )

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a subparser.

    Args:
        parser: The ArgumentParser to add arguments to.
    """
    parser.add_argument(
        "--public",
        action="store_true",
        help="Create a public repository (default is private)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the Jules session until completion"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for watching session (default: 1800)"
    )


def parse_args() -> Any:
    """Parse command line arguments.

    Returns:
        The parsed arguments namespace.
    """
    parser = create_parser()
    return parser.parse_args()
