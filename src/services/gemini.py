import os
import json
import logging
from google import genai
from google.genai import types

from src.core.models import IdeaResponse, ProjectScaffold
from src.utils.errors import ConfigurationError, GenerationError


logger = logging.getLogger(__name__)

# Category-specific prompt templates
CATEGORY_PROMPTS = {
    "web_app": "Generate a creative web application idea. Focus on modern frontend frameworks and responsive design.",
    "cli_tool": "Generate a useful command-line tool idea. Focus on developer productivity and Unix philosophy.",
    "api_service": "Generate a RESTful API service idea. Focus on microservices architecture and scalability.",
    "mobile_app": "Generate a mobile application idea. Focus on user experience and cross-platform compatibility.",
    "automation": "Generate an automation tool idea. Focus on workflow optimization and integration capabilities.",
    "ai_ml": "Generate an AI/ML application idea. Focus on practical use cases and accessible interfaces.",
    "default": "Generate a creative, unique, and useful software application idea."
}

class GeminiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY environment variable is not set",
                tip="Get your API key from https://aistudio.google.com/app/apikey and add it to your .env file."
            )
        
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1beta'}
        )
        self.model_name = "gemini-3-pro-preview"

    def _generate_content(self, prompt: str, response_schema: type, error_tip: str = None):
        """Helper to generate content and parse JSON response."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
                response_mime_type="application/json",
                response_schema=response_schema
            ),
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise GenerationError(
                f"Failed to parse Gemini response: {e}",
                tip=error_tip or "The AI model returned invalid JSON. Please try again."
            )

    def generate_idea(self, category: str = None):
        """Generates a unique software idea using Gemini 3.

        Args:
            category: Optional category to target (web_app, cli_tool, api_service, mobile_app, automation, ai_ml)
        """
        base_prompt = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["default"])
        prompt = f"{base_prompt} Include recommended tech stack and key MVP features."

        return self._generate_content(
            prompt,
            IdeaResponse,
            error_tip="The AI model returned invalid JSON. Please try again or try a different category."
        )

    def extract_idea_from_text(self, text):
        """Extracts the core app idea from the provided text."""
        # Truncate text if it's too long to avoid token limits
        max_chars = 100000 
        truncated_text = text[:max_chars]
        
        prompt = f"""
        Analyze the following text from a website and extract the core software application idea or product concept described.
        Summarize it into a clear, actionable project description suitable for a developer to start building.
        
        Text content:
        {truncated_text}
        """
        
        return self._generate_content(
            prompt,
            IdeaResponse,
            error_tip="The AI model returned invalid JSON while analyzing the website content."
        )

    def generate_project_scaffold(self, idea_data: dict, max_retries: int = 2):
        """Generates a complete MVP project scaffold for the given idea.
        
        Args:
            idea_data: Dict with title, description, slug, tech_stack, features
            max_retries: Number of retries on failure (default: 2)
        
        Returns:
            ProjectScaffold with files, requirements, and run command
        """
        # Developer-ready MVP prompt
        prompt = f"""
Generate a DEVELOPER-READY MVP project scaffold for:

**Project:** {idea_data['title']}
**Description:** {idea_data['description'][:500]}

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
        
        for attempt in range(max_retries + 1):
            try:
                return self._generate_content(prompt, ProjectScaffold)
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Scaffold generation attempt {attempt + 1} failed: {e}. Retrying...")
                    continue
                else:
                    logger.error(f"Scaffold generation failed after {max_retries + 1} attempts: {e}")
                    # Return minimal fallback scaffold
                    return self._get_fallback_scaffold(idea_data)
    
    def _get_fallback_scaffold(self, idea_data: dict) -> dict:
        """Returns a developer-ready fallback scaffold when generation fails."""
        title = idea_data['title']
        desc = idea_data['description'][:200]
        
        return {
            "files": [
                {
                    "path": "main.py",
                    "content": f'''#!/usr/bin/env python3
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

