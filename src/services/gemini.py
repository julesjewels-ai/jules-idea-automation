import os
import json
import logging
from google import genai
from google.genai import types

from src.core.models import IdeaResponse, ProjectScaffold
from src.services.templates import (
    CATEGORY_PROMPTS,
    get_extraction_prompt,
    get_fallback_scaffold,
    get_scaffold_prompt
)
from src.utils.errors import ConfigurationError, GenerationError


logger = logging.getLogger(__name__)


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

    def generate_idea(self, category: str | None = None):
        """Generates a unique software idea using Gemini 3.
        
        Args:
            category: Optional category to target (web_app, cli_tool, api_service, mobile_app, automation, ai_ml)
        """
        base_prompt = CATEGORY_PROMPTS.get(category or "default", CATEGORY_PROMPTS["default"])
        prompt = f"{base_prompt} Include recommended tech stack and key MVP features."
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
                response_mime_type="application/json",
                response_schema=IdeaResponse
            ),
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise GenerationError(
                f"Failed to parse Gemini response: {e}",
                tip="The AI model returned invalid JSON. Please try again or try a different category."
            )

    def extract_idea_from_text(self, text):
        """Extracts the core app idea from the provided text."""
        # Truncate text if it's too long to avoid token limits
        max_chars = 100000 
        truncated_text = text[:max_chars]
        
        prompt = get_extraction_prompt(truncated_text)
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
             config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
                response_mime_type="application/json",
                response_schema=IdeaResponse
            ),
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise GenerationError(
                f"Failed to parse Gemini response: {e}",
                tip="The AI model returned invalid JSON while analyzing the website content."
            )

    def generate_project_scaffold(self, idea_data: dict, max_retries: int = 2):
        """Generates a complete MVP project scaffold for the given idea.
        
        Args:
            idea_data: Dict with title, description, slug, tech_stack, features
            max_retries: Number of retries on failure (default: 2)
        
        Returns:
            ProjectScaffold with files, requirements, and run command
        """
        prompt = get_scaffold_prompt(
            idea_data['title'],
            idea_data['description'][:500]
        )
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(include_thoughts=True),
                        response_mime_type="application/json",
                        response_schema=ProjectScaffold
                    ),
                )
                return json.loads(response.text)
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Scaffold generation attempt {attempt + 1} failed: {e}. Retrying...")
                    continue
                else:
                    logger.error(f"Scaffold generation failed after {max_retries + 1} attempts: {e}")
                    # Return minimal fallback scaffold
                    return get_fallback_scaffold(
                        idea_data['title'],
                        idea_data['description'][:200]
                    )

