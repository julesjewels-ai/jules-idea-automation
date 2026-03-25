#!/usr/bin/env python3
"""Jules Automation Tool - Entry Point.

This is the main entry point for the CLI.
It handles only orchestration - all business logic is in src/
"""

import re
import sys
import traceback

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.cli.commands import dispatch_command  # noqa: E402
from src.cli.parser import create_parser  # noqa: E402
from src.utils.errors import AppError  # noqa: E402
from src.utils.reporter import Colors, print_panel  # noqa: E402


def _format_error_title(exc: BaseException) -> str:
    """Convert an exception class name to a human-readable panel title.

    Examples:
        ConfigurationError  -> "Configuration Error"
        GitHubApiError      -> "Git Hub Api Error"  (camelCase split)
        RuntimeError        -> "Runtime Error"
    """
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", type(exc).__name__)


def _maybe_print_traceback(verbose: bool, *, hint_on_silence: bool = False) -> None:
    """Print the current traceback to stderr when verbose is enabled.

    Args:
        verbose: If True, print the full traceback.
        hint_on_silence: If True and not verbose, print a brief hint directing
            the user to re-run with --verbose.
    """
    if verbose:
        print(file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    elif hint_on_silence:
        print(
            f"  {Colors.BOLD}💡 Tip:{Colors.ENDC} Run with --verbose to see the full traceback.",
            file=sys.stderr,
        )


def main() -> None:
    """Main entry point - orchestration only."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n💡 Tip: Run 'python main.py guide' for an interactive tutorial\n")
        sys.exit(1)

    verbose = getattr(args, "verbose", False)

    try:
        dispatch_command(args)
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except AppError as e:
        tip_msg = f"\n\n{Colors.BOLD}💡 Tip:{Colors.ENDC}\n{e.tip}" if e.tip else ""
        print_panel(
            f"{str(e)}{tip_msg}",
            title=_format_error_title(e),
            color=Colors.RED,
        )
        _maybe_print_traceback(verbose)
        sys.exit(1)
    except Exception as e:
        message = str(e) if str(e) else type(e).__name__
        print_panel(
            message,
            title="Unexpected Error",
            color=Colors.RED,
        )
        _maybe_print_traceback(verbose, hint_on_silence=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
