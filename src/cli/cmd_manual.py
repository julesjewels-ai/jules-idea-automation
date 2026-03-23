"""Handler for the 'manual' command."""

from __future__ import annotations

from argparse import Namespace

from src.cli._shared import execute_and_watch


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

    execute_and_watch(args, idea_data)
