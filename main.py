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
    except Exception as e:
        from src.utils.reporter import print_panel, Colors
        from src.services.jules import JulesAPIError

        if isinstance(e, JulesAPIError):
            print_panel(
                str(e),
                title="Jules API Error",
                color=Colors.FAIL,
                width=70
            )
        else:
            if hasattr(e, 'response') and e.response is not None:
                print(f"HTTP Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
