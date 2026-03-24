"""Command handlers for the CLI.

Each command is implemented in its own module under ``src.cli``.
This file re-exports them and provides the top-level ``dispatch_command``
function used by the argument parser.
"""

from __future__ import annotations

import sys
from argparse import Namespace

from src.cli.cmd_agent import handle_agent
from src.cli.cmd_manual import handle_manual
from src.cli.cmd_paste import handle_paste
from src.cli.cmd_watch import handle_list_sources, handle_status
from src.cli.cmd_website import handle_website

# Re-export command-level symbols for backwards compatibility
# (tests and external code may import directly from src.cli.commands)
__all__ = [
    "handle_agent",
    "handle_website",
    "handle_paste",
    "handle_manual",
    "handle_status",
    "handle_list_sources",
    "handle_guide",
    "dispatch_command",
]


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

    if isinstance(workflow, str) and workflow in guides:
        guides[workflow]()
    else:
        print_welcome_guide()
        print_examples()


def dispatch_command(args: Namespace) -> None:
    """Dispatch to the appropriate command handler."""
    from src.utils.config import validate_env_keys

    validate_env_keys(args.command, is_demo=getattr(args, "demo", False))

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
