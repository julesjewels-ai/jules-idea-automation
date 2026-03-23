"""Handler for the 'paste' command."""

from __future__ import annotations

import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from src.cli._shared import build_gemini_client, execute_and_watch
from src.utils.reporter import Spinner


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
            "Clipboard reading requires 'pbpaste' (macOS only). "
            "On other systems, use --file or pipe via stdin instead."
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
    # Determine source label and spinner message for UX feedback
    if getattr(args, "clipboard", False):
        source_label = "📋 clipboard"
        read_msg = "Reading clipboard…"
    elif getattr(args, "file_path", None):
        source_label = f"📄 {args.file_path}"
        read_msg = f"Reading {args.file_path}…"
    elif getattr(args, "content_source", None) == "-":
        source_label = "⎎ stdin"
        read_msg = ""  # stdin/interactive are inherently visible, no spinner needed
    else:
        source_label = "⌨️  interactive"
        read_msg = ""

    if read_msg:
        with Spinner(read_msg, success_message=f"Content read from {source_label}"):
            text = _read_paste_content(args)
    else:
        text = _read_paste_content(args)

    # Show content preview so user knows what was captured
    preview = text[:200].replace("\n", " ")
    if len(text) > 200:
        preview += "..."
    print(f"\n✔ Read {len(text):,} chars from {source_label}")
    print(f"  Preview: {preview}\n")

    gemini = build_gemini_client()
    with Spinner("Extracting idea with Gemini…", success_message="Idea extracted"):
        idea_data = gemini.extract_idea_from_text(text)

    execute_and_watch(args, idea_data, gemini=gemini)
