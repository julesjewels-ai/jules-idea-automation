"""Templates for Gemini service."""

CATEGORY_PROMPTS = {
    "web_app": "Generate a creative web application idea. Focus on modern frontend frameworks and responsive design.",
    "cli_tool": "Generate a useful command-line tool idea. Focus on developer productivity and Unix philosophy.",
    "api_service": "Generate a RESTful API service idea. Focus on microservices architecture and scalability.",
    "mobile_app": "Generate a mobile application idea. Focus on user experience and cross-platform compatibility.",
    "automation": "Generate an automation tool idea. Focus on workflow optimization and integration capabilities.",
    "ai_ml": "Generate an AI/ML application idea. Focus on practical use cases and accessible interfaces.",
    "default": "Generate a creative, unique, and useful software application idea."
}

def get_scaffold_prompt(title: str, description: str) -> str:
    """Returns the prompt for generating a project scaffold."""
    return f"""
Generate a DEVELOPER-READY MVP project scaffold for:

**Project:** {title}
**Description:** {description}

Create a complete, immediately-runnable project with these files:

## Core Application
1. main.py - Entry point with argparse CLI (--help, --version flags)
2. src/__init__.py - Package marker
3. src/core/__init__.py - Package marker
4. src/core/app.py - Main business logic class with clear docstrings

## Developer Experience
5. Makefile - With targets: install, run, test, clean
6. .env.example - Sample environment variables (if any needed)
7. .gitignore - Python + venv + IDE + .env patterns

## Testing
8. tests/__init__.py - Package marker
9. tests/test_core.py - Basic unit test using pytest

## Requirements:
- Include 'pytest' in the requirements list
- Makefile 'install' should: create venv, install deps
- Makefile 'run' should: activate venv and run main.py
- Makefile 'test' should: run pytest
- Tests should pass immediately when run
- Use type hints throughout
- Each file should have a module docstring
"""


def get_extraction_prompt(text: str) -> str:
    """Returns the prompt for extracting an idea from text."""
    return f"""
        Analyze the following text from a website and extract the core software application idea or product concept described.
        Summarize it into a clear, actionable project description suitable for a developer to start building.

        Text content:
        {text}
        """


def get_fallback_scaffold(title: str, description: str) -> dict:
    """Returns a developer-ready fallback scaffold when generation fails."""
    return {
        "files": [
            {
                "path": "main.py",
                "content": f'''#!/usr/bin/env python3
"""
{title}

{description}
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
''',
                "description": "Main entry point with CLI"
            },
            {
                "path": "src/__init__.py",
                "content": '"""Source package."""\n',
                "description": "Package marker"
            },
            {
                "path": "src/core/__init__.py",
                "content": '"""Core application package."""\n',
                "description": "Package marker"
            },
            {
                "path": "src/core/app.py",
                "content": f'''"""Core application logic for {title}."""


class App:
    """Main application class."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.name = "{title}"

    def run(self) -> None:
        """Run the main application logic."""
        print(f"Welcome to {{self.name}}")
        # TODO: Implement main logic
''',
                "description": "Main business logic"
            },
            {
                "path": "Makefile",
                "content": '''.PHONY: install run test clean

install:
\tpython -m venv venv
\t. venv/bin/activate && pip install -r requirements.txt

run:
\t. venv/bin/activate && python main.py

test:
\t. venv/bin/activate && pytest tests/ -v

clean:
\trm -rf __pycache__ .pytest_cache
\tfind . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
''',
                "description": "Development commands"
            },
            {
                "path": ".env.example",
                "content": f'''# {title} - Environment Variables
# Copy to .env and fill in values

# Add your environment variables here
# EXAMPLE_API_KEY=your_key_here
''',
                "description": "Environment template"
            },
            {
                "path": ".gitignore",
                "content": """# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
.env
*.egg-info/
dist/
build/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp
""",
                "description": "Git ignore file"
            },
            {
                "path": "tests/__init__.py",
                "content": '"""Test package."""\n',
                "description": "Test package marker"
            },
            {
                "path": "tests/test_core.py",
                "content": f'''"""Tests for core application."""

from src.core.app import App


def test_app_init() -> None:
    """Test app initialization."""
    app = App()
    assert app.name == "{title}"


def test_app_run(capsys) -> None:
    """Test app run output."""
    app = App()
    app.run()
    captured = capsys.readouterr()
    assert "Welcome to" in captured.out
''',
                "description": "Core unit tests"
            }
        ],
        "requirements": ["pytest"],
        "run_command": "python main.py"
    }
