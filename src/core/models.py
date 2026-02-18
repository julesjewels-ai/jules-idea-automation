"""Pydantic models for the Jules Automation Tool."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class IdeaResponse(BaseModel):
    """Represents a generated software idea."""

    title: str = Field(description="The name of the software idea.")
    description: str = Field(description="A detailed description of the idea.")
    slug: str = Field(description="A kebab-case string for GitHub repository name.")
    tech_stack: list[str] = Field(default_factory=list, description="Recommended technologies.")
    features: list[str] = Field(default_factory=list, description="Key MVP features.")


class ProjectFile(BaseModel):
    """Represents a single file in a project scaffold."""

    path: str = Field(description="Relative file path from project root.")
    content: str = Field(description="Complete file content.")
    description: str = Field(description="Brief description of the file.")


class ProjectScaffold(BaseModel):
    """Represents a complete project scaffold."""

    files: list[ProjectFile] = Field(description="List of files to create.")
    requirements: list[str] = Field(default_factory=list, description="Python dependencies.")
    run_command: str = Field(default="python main.py", description="Command to run the app.")

    @classmethod
    def create_fallback_scaffold(cls, title: str, description: str) -> "ProjectScaffold":
        """Create a default scaffold when generation fails."""
        desc = description[:200]

        return cls(
            files=[
                ProjectFile(
                    path="main.py",
                    content=f'''#!/usr/bin/env python3
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
''',
                    description="Main entry point with CLI"
                ),
                ProjectFile(
                    path="src/__init__.py",
                    content='"""Source package."""\n',
                    description="Package marker"
                ),
                ProjectFile(
                    path="src/core/__init__.py",
                    content='"""Core application package."""\n',
                    description="Package marker"
                ),
                ProjectFile(
                    path="src/core/app.py",
                    content=f'''"""Core application logic for {title}."""


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
                    description="Main business logic"
                ),
                ProjectFile(
                    path="Makefile",
                    content='''.PHONY: install run test clean

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
                    description="Development commands"
                ),
                ProjectFile(
                    path=".env.example",
                    content=f'''# {title} - Environment Variables
# Copy to .env and fill in values

# Add your environment variables here
# EXAMPLE_API_KEY=your_key_here
''',
                    description="Environment template"
                ),
                ProjectFile(
                    path=".gitignore",
                    content="""# Python
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
                    description="Git ignore file"
                ),
                ProjectFile(
                    path="tests/__init__.py",
                    content='"""Test package."""\n',
                    description="Test package marker"
                ),
                ProjectFile(
                    path="tests/test_core.py",
                    content=f'''"""Tests for core application."""

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
                    description="Core unit tests"
                )
            ],
            requirements=["pytest"],
            run_command="python main.py"
        )


class WorkflowResult(BaseModel):
    """Result of the idea-to-repository workflow."""

    idea: IdeaResponse
    repo_url: str
    session_id: Optional[str] = None
    session_url: Optional[str] = None
    pr_url: Optional[str] = None
