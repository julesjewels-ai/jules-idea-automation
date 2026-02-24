#!/usr/bin/env python3
"""
{title}

{desc}
"""

import argparse
from src.core.app import App


def main() -> None:
    """Main entry point with CLI support."""
    parser = argparse.ArgumentParser(description="{title}")
    parser.add_argument("--version", action="version", version="0.1.0")
    args = parser.parse_args()

    app = App()
    app.run()


if __name__ == "__main__":
    main()
