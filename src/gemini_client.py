import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class IdeaResponse(BaseModel):
    title: str = Field(description="The name of the software idea.")
    description: str = Field(description="A detailed description of the idea, highlighting core functionality and value proposition.")
    slug: str = Field(description="A short, kebab-case string suitable for a GitHub repository name (e.g., 'awesome-crm-tool').")
    tech_stack: list[str] = Field(description="Recommended technologies and frameworks for implementing this idea.")
    features: list[str] = Field(description="Key features to implement in the MVP.")


class ProjectFile(BaseModel):
    path: str = Field(description="Relative file path from project root (e.g., 'src/core/service.py')")
    content: str = Field(description="Complete file content with proper formatting")
    description: str = Field(description="Brief description of what this file does")


class ProjectScaffold(BaseModel):
    files: list[ProjectFile] = Field(description="List of files to create for the MVP")
    requirements: list[str] = Field(description="Python package dependencies (for requirements.txt)")
    run_command: str = Field(description="Command to run the application (e.g., 'python main.py')")


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

    def generate_project_scaffold(self, idea_data: dict):
        """Generates a complete MVP project scaffold for the given idea.
        
        Args:
            idea_data: Dict with title, description, slug, tech_stack, features
        
        Returns:
            ProjectScaffold with files, requirements, and run command
        """
        prompt = f"""
Generate a complete, working MVP project scaffold for this software idea:

**Project:** {idea_data['title']}
**Description:** {idea_data['description']}
**Tech Stack:** {', '.join(idea_data.get('tech_stack', ['Python']))}
**Features:** {', '.join(idea_data.get('features', []))}

Requirements:
1. Follow SOLID principles strictly
2. Keep main.py clean - orchestration ONLY, no business logic
3. Create a src/ directory with modular components:
   - src/core/ - Business logic and domain models
   - src/services/ - External integrations and services  
   - src/utils/ - Helper functions and utilities
4. Include proper __init__.py files
5. Add a .gitignore with Python defaults
6. Create a README.md with setup instructions
7. Generate working, runnable code (not just stubs)
8. Use type hints throughout
9. Include basic error handling
10. Keep it minimal but functional - this is an MVP

Generate the complete file contents for each file.
"""
        
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
