#!/usr/bin/env python3
"""
Jules Automation Tool - Entry Point

This is the main entry point for the CLI.
It handles only orchestration - all business logic is in src/
"""

import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.cli.parser import create_parser
from src.cli.commands import dispatch_command
from src.utils.errors import AppError
from src.utils.reporter import print_panel, Colors


def main() -> None:
    """Main entry point - orchestration only."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\n💡 Tip: Run 'python main.py guide' for an interactive tutorial\n")
        sys.exit(1)
    
    try:
        dispatch_command(args)
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except AppError as e:
        tip_msg = f"\n\n{Colors.BOLD}💡 Tip:{Colors.ENDC}\n{e.tip}" if e.tip else ""

        # Format title from class name: ConfigurationError -> Configuration Error
        title = type(e).__name__.replace("Error", " Error")

        print_panel(
            f"{str(e)}{tip_msg}",
            title=title,
            color=Colors.FAIL
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
