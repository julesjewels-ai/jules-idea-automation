import os
import json
from google import genai
from google.genai import types

from src.core.models import IdeaResponse, ProjectFile, ProjectScaffold



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
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1beta'}
        )
        self.model_name = "gemini-3-pro-preview"

    def generate_idea(self, category: str = None):
        """Generates a unique software idea using Gemini 3.
        
        Args:
            category: Optional category to target (web_app, cli_tool, api_service, mobile_app, automation, ai_ml)
        """
        base_prompt = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["default"])
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
        return json.loads(response.text)

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
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
             config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
                response_mime_type="application/json",
                response_schema=IdeaResponse
            ),
        )
        return json.loads(response.text)

    def generate_project_scaffold(self, idea_data: dict, max_retries: int = 2):
        """Generates a complete MVP project scaffold for the given idea.
        
        Args:
            idea_data: Dict with title, description, slug, tech_stack, features
            max_retries: Number of retries on failure (default: 2)
        
        Returns:
            ProjectScaffold with files, requirements, and run command
        """
        # Simplified prompt for faster generation
        prompt = f"""
Generate a minimal MVP project scaffold for:

**Project:** {idea_data['title']}
**Description:** {idea_data['description'][:500]}

Create these files:
1. main.py - Orchestration only, imports from src/
2. src/__init__.py - Empty
3. src/core/__init__.py - Empty  
4. src/core/app.py - Main business logic class
5. .gitignore - Python defaults

Keep code simple and functional. Use type hints. Max 50 lines per file.
"""
        
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
                    print(f"  Scaffold generation attempt {attempt + 1} failed, retrying...")
                    continue
                else:
                    print(f"  Scaffold generation failed after {max_retries + 1} attempts: {e}")
                    # Return minimal fallback scaffold
                    return self._get_fallback_scaffold(idea_data)
    
    def _get_fallback_scaffold(self, idea_data: dict) -> dict:
        """Returns a minimal fallback scaffold when generation fails."""
        return {
            "files": [
                {
                    "path": "main.py",
                    "content": f'''#!/usr/bin/env python3
"""
{idea_data['title']}
{idea_data['description'][:200]}
"""

def main():
    print("Welcome to {idea_data['title']}")
    # TODO: Implement main logic

if __name__ == "__main__":
    main()
''',
                    "description": "Main entry point"
                },
                {
                    "path": "src/__init__.py",
                    "content": '"""Core package."""\n',
                    "description": "Package init"
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
""",
                    "description": "Git ignore file"
                }
            ],
            "requirements": [],
            "run_command": "python main.py"
        }

