from __future__ import annotations

import hashlib
import json
import logging
import os
import warnings
from typing import Any
from xml.sax.saxutils import escape

# Suppress Pydantic warning from google-genai 0.8.0 about 'any' as a type
warnings.filterwarnings(
    "ignore",
    message=".*<built-in function any> is not a Python type.*",
    category=UserWarning,
    module="pydantic",
)

from google import genai
from google.genai import errors, types

from src.core.interfaces import CacheProvider
from src.core.models import FeatureMapResponse, IdeaResponse, ProjectScaffold
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
    "default": "Generate a creative, unique, and useful software application idea.",
}


class GeminiClient:
    """Client for the Google Gemini API, handling idea generation and project scaffolding."""

    def __init__(self, api_key: str | None = None, cache_provider: CacheProvider | None = None) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY environment variable is not set",
                tip="Get your API key from https://aistudio.google.com/app/apikey and add it to your .env file.",
            )

        self.client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
        self.models = ["gemini-2.5-flash"]
        self.cache_provider = cache_provider

    def _map_api_error(self, e: errors.APIError) -> GenerationError:
        """Maps Gemini API errors to user-friendly GenerationError."""
        err_msg_lower = str(e).lower()

        error_tips = (
            (
                ("api key not valid", "400"),
                "Your GEMINI_API_KEY seems invalid. Check your .env file.",
            ),
            (("429", "quota"), "You have exceeded your API quota. Try again later."),
            (("403",), "You don't have permission to access this model."),
            (
                ("503", "unavailable"),
                "The Gemini API is currently overloaded. Please wait a few minutes and try again.",
            ),
        )

        for keys, tip in error_tips:
            if any(k in err_msg_lower for k in keys):
                return GenerationError(f"Gemini API Error: {e}", tip=tip)

        return GenerationError(
            f"Gemini API Error: {e}",
            tip="Check your internet connection and API status.",
        )

    def _get_cached_content(self, prompt: str, schema: Any) -> tuple[dict[str, Any] | None, str]:
        """Checks the cache for existing content and returns the data and cache key."""
        if not self.cache_provider:
            return None, ""

        schema_name = getattr(schema, "__name__", str(schema))
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        cache_key = f"{self.models[0]}:{prompt_hash}:{schema_name}"

        cached_data = self.cache_provider.get(cache_key)
        if cached_data:
            logger.info("Cache hit for key: %s", cache_key)
            if hasattr(schema, "model_validate"):
                return schema.model_validate(cached_data).model_dump(), cache_key
            return cached_data, cache_key

        return None, cache_key

    def _process_api_response(self, text: str | None, schema: Any, cache_key: str, error_tip: str) -> dict[str, Any]:
        """Parses, caches, and validates the API response."""
        try:
            raw = json.loads(text or "")
        except json.JSONDecodeError as e:
            raise GenerationError(f"Failed to parse Gemini response: {e}", tip=error_tip)

        if self.cache_provider and cache_key:
            self.cache_provider.set(cache_key, raw)

        if hasattr(schema, "model_validate"):
            return schema.model_validate(raw).model_dump()  # type: ignore[no-any-return]
        return raw  # type: ignore[no-any-return]

    def _fetch_from_api(self, prompt: str, schema: Any, error_tip: str, cache_key: str) -> dict[str, Any]:
        """Fetches content from Gemini API and handles errors/caching."""
        last_api_error = None
        for i, model in enumerate(self.models):
            try:
                use_thinking = "pro" in model or "think" in model
                config_kwargs: dict[str, Any] = {
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                }
                if use_thinking:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(include_thoughts=True)

                if i > 0:
                    logger.warning("Primary model failed. Falling back to %s...", model)

                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                return self._process_api_response(response.text, schema, cache_key, error_tip)
            except errors.APIError as e:
                err_msg = str(e)
                last_api_error = e
                is_unavailable = "503" in err_msg or "UNAVAILABLE" in err_msg
                is_quota_exhausted = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                if is_unavailable or is_quota_exhausted:
                    reason = "503 UNAVAILABLE" if is_unavailable else "429 RESOURCE_EXHAUSTED"
                    logger.warning("Model %s returned %s.", model, reason)
                    continue
                raise self._map_api_error(e)
            except GenerationError:
                raise
            except Exception as e:
                raise GenerationError(
                    f"Unexpected error during generation: {e}",
                    tip="Check your network connection and configuration.",
                )

        if last_api_error:
            raise self._map_api_error(last_api_error)

        raise GenerationError(
            "All model generation attempts failed.",
            tip="Check your internet connection and API status.",
        )

    def _generate_content(self, prompt: str, schema: Any, error_tip: str) -> dict[str, Any]:
        """Helper to generate content with consistent configuration and error handling."""
        # Check cache if available
        cached_data, cache_key = self._get_cached_content(prompt, schema)
        if cached_data:
            return cached_data

        return self._fetch_from_api(prompt, schema, error_tip, cache_key)

    def generate_idea(self, category: str | None = None) -> dict[str, Any]:
        """Generates a unique software idea using Gemini 3.

        Args:
        ----
            category: Optional category to target (web_app, cli_tool, api_service, mobile_app, automation, ai_ml)

        """
        base_prompt = CATEGORY_PROMPTS.get(category or "default", CATEGORY_PROMPTS["default"])
        prompt = f"{base_prompt} Include recommended tech stack and key MVP features."

        return self._generate_content(
            prompt,
            IdeaResponse,
            "The AI model returned invalid JSON. Please try again or try a different category.",
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
            "The AI model returned invalid JSON while analyzing the website content.",
        )

    def generate_project_scaffold(self, idea_data: dict[str, Any], max_retries: int = 2) -> dict[str, Any]:
        """Generates a complete MVP project scaffold for the given idea.

        Args:
        ----
            idea_data: Dict with title, description, slug, tech_stack, features
            max_retries: Number of retries on failure (default: 2)

        Returns:
        -------
            ProjectScaffold with files, requirements, and run command

        """
        # Sanitize inputs
        safe_title = escape(idea_data["title"])
        safe_desc = escape(idea_data["description"][:500])

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
                    "Failed to generate valid project scaffold.",
                )
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        "Scaffold generation attempt %d failed: %s. Retrying...",
                        attempt + 1,
                        e,
                    )
                    continue
                else:
                    logger.error(
                        "Scaffold generation failed after %d attempts: %s",
                        max_retries + 1,
                        e,
                    )
                    # Return minimal fallback scaffold
                    return ProjectScaffold.create_fallback_scaffold(
                        idea_data["title"], idea_data["description"]
                    ).model_dump()

        raise GenerationError("Failed to generate project scaffold.")

    @staticmethod
    def _summarize_scaffold_files(files: list[dict[str, Any]], max_content_len: int = 500) -> str:
        """Build a concise summary of scaffold files for the feature map prompt."""
        lines: list[str] = []
        for f in files:
            path = f.get("path", "unknown")
            desc = f.get("description", "")
            content = f.get("content", "")
            # Truncate content to keep prompt within reasonable size
            preview = content[:max_content_len].rstrip()
            if len(content) > max_content_len:
                preview += "\n... (truncated)"
            lines.append(f"### {path}\n**Description:** {desc}\n```\n{preview}\n```")
        return "\n\n".join(lines)

    def generate_feature_maps(self, idea_data: dict[str, Any], scaffold_files: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate project-specific MVP and Production feature maps.

        Uses the actual scaffold code as context so every feature item
        references real file paths, classes, and dependencies.

        Args:
        ----
            idea_data: Dict with title, description, slug, tech_stack, features
            scaffold_files: List of scaffold file dicts with path, content, description

        Returns:
        -------
            FeatureMapResponse with mvp_features and production_features

        """
        safe_title = escape(idea_data.get("title", "Untitled"))
        safe_desc = escape(idea_data.get("description", "")[:500])
        tech_stack = ", ".join(idea_data.get("tech_stack", [])) or "Not specified"
        features = ", ".join(idea_data.get("features", [])) or "Not specified"

        files_summary = self._summarize_scaffold_files(scaffold_files)

        prompt = f"""You are a senior software architect. Analyze this project and generate two feature maps.

## Project
**Title:** <project_title>{safe_title}</project_title>
**Description:** <project_description>{safe_desc}</project_description>
**Tech Stack:** {tech_stack}
**High-Level Features:** {features}

## Actual Project Files
{files_summary}

---

## Your Task

Generate TWO feature maps based on the ACTUAL project code above:

### 1. MVP Features (mvp_features)
Concrete features to make this a working, demonstrable prototype. Each item MUST:
- Reference actual file paths from the project (e.g., "Add X to `src/core/app.py`")
- Include specific acceptance criteria a developer can test
- Be ordered from most critical (P0) to nice-to-have (P2)
- Include project setup items (env setup, basic tests, demo data)

Generate 8-15 MVP items.

### 2. Production Features (production_features)
Infrastructure and hardening items needed to deploy at scale. CRITICAL RULES:
- ONLY include items RELEVANT to this specific project type
- A CLI tool does NOT need "health check endpoints" or "CORS headers"
- A web API does NOT need "CLI argument validation"
- A data pipeline does NOT need "rate limiting"
- Reference actual project files where changes would be made
- Be specific: "Add retry logic to the HTTP client in `src/core/app.py`" not "Add error handling"

Generate 15-25 production items across relevant categories such as:
error handling, testing, CI/CD, security, observability, deployment, documentation, performance.
Skip any category that doesn't apply to this project type.

### Priority Guide
| Label | MVP Meaning | Production Meaning |
|-------|------------|-------------------|
| P0 | Prototype doesn't work without it | Blocks production deployment |
| P1 | Important for a convincing demo | Needed for reliable operation |
| P2 | Improves the prototype | Improves quality, schedule when possible |
| P3 | (rarely used) | Nice-to-have, future-looking |
"""

        try:
            return self._generate_content(
                prompt,
                FeatureMapResponse,
                "Failed to generate feature maps. Static fallback will be used.",
            )
        except Exception as e:
            logger.warning("Feature map generation failed: %s. Returning empty maps.", e)
            return FeatureMapResponse(mvp_features=[], production_features=[]).model_dump()
