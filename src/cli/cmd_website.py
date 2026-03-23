"""Handler for the 'website' command."""

from __future__ import annotations

from argparse import Namespace

from src.cli._shared import build_gemini_client, execute_and_watch
from src.utils.reporter import Spinner


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

    gemini = build_gemini_client()
    with Spinner("Extracting idea with Gemini...", success_message="Idea extracted"):
        idea_data = gemini.extract_idea_from_text(text)

    execute_and_watch(args, idea_data, gemini=gemini)
