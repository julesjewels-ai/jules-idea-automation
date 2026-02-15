from __future__ import annotations

import os
import json
import logging
from typing import Optional, Any
from xml.sax.saxutils import escape
from google import genai
from google.genai import types, errors

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
    """Client for the Google Gemini API, handling idea generation and project scaffolding."""

    def __init__(self, api_key: Optional[str] = None) -> None:
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

    def _map_api_error(self, e: errors.APIError) -> GenerationError:
        """Maps Gemini API errors to user-friendly GenerationError."""
        tip = "Check your internet connection and API status."
        err_msg = str(e)

        if "API key not valid" in err_msg or "400" in err_msg:
            tip = "Your GEMINI_API_KEY seems invalid. Check your .env file."
        elif "429" in err_msg or "quota" in err_msg.lower():
            tip = "You have exceeded your API quota. Try again later."
        elif "403" in err_msg:
            tip = "You don't have permission to access this model."

        return GenerationError(f"Gemini API Error: {e}", tip=tip)

    def _generate_content(self, prompt: str, schema: Any, error_tip: str) -> dict[str, Any]:
        """Helper to generate content with consistent configuration and error handling."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=True),
                    response_mime_type="application/json",
                    response_schema=schema
                ),
            )
            return json.loads(response.text or "")  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise GenerationError(
                f"Failed to parse Gemini response: {e}",
                tip=error_tip
            )
        except errors.APIError as e:
            raise self._map_api_error(e)
        except Exception as e:
            raise GenerationError(
                f"Unexpected error during generation: {e}",
                tip="Check your network connection and configuration."
            )

    def generate_idea(self, category: Optional[str] = None) -> dict[str, Any]:
        """Generates a unique software idea using Gemini 3.

        Args:
            category: Optional category to target (web_app, cli_tool, api_service, mobile_app, automation, ai_ml)
        """
        base_prompt = CATEGORY_PROMPTS.get(
            category or "default", CATEGORY_PROMPTS["default"])
        prompt = f"{base_prompt} Include recommended tech stack and key MVP features."

        return self._generate_content(
            prompt,
            IdeaResponse,
            "The AI model returned invalid JSON. Please try again or try a different category."
        )

    def extract_idea_from_text(self, text: str) -> dict[str, Any]:
        """Extracts the core app idea from the provided text."""
        # Truncate text if it's too long to avoid token limits
        max_chars = 100000
        truncated_text = text[:max_chars]

        # Escape user content to prevent prompt injection
        safe_text = escape(truncated_text)

        prompt = f"""
        Analyze the following text provided in the <text_content> tags.
        Extract the core software application idea or product concept described.
        Summarize it into a clear, actionable project description suitable for a developer to start building.
        
        <text_content>
        {safe_text}
        </text_content>
        """

        return self._generate_content(
            prompt,
            IdeaResponse,
            "The AI model returned invalid JSON while analyzing the website content."
        )

    def generate_project_scaffold(self, idea_data: dict[str, Any], max_retries: int = 2) -> dict[str, Any]:
        """Generates a complete MVP project scaffold for the given idea.

        Args:
            idea_data: Dict with title, description, slug, tech_stack, features
            max_retries: Number of retries on failure (default: 2)

        Returns:
            ProjectScaffold with files, requirements, and run command
        """
        # Sanitize inputs
        safe_title = escape(idea_data['title'])
        safe_desc = escape(idea_data['description'][:500])

        # Developer-ready MVP prompt
        prompt = f"""
Generate a DEVELOPER-READY MVP project scaffold for:

**Project:** <project_title>{safe_title}</project_title>
**Description:** <project_description>{safe_desc}</project_description>

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
                return self._generate_content(
                    prompt,
                    ProjectScaffold,
                    "Failed to generate valid project scaffold."
                )
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        f"Scaffold generation attempt {attempt + 1} failed: {e}. Retrying...")
                    continue
                else:
                    logger.error(
                        f"Scaffold generation failed after {max_retries + 1} attempts: {e}")
                    # Return minimal fallback scaffold
                    return ProjectScaffold.create_fallback_scaffold(
                        idea_data['title'],
                        idea_data['description']
                    ).model_dump()

        raise GenerationError("Failed to generate project scaffold.")
