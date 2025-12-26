import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class IdeaResponse(BaseModel):
    title: str = Field(description="The name of the software idea.")
    description: str = Field(description="A detailed description of the idea, highlighting core functionality and value proposition.")
    slug: str = Field(description="A short, kebab-case string suitable for a GitHub repository name (e.g., 'awesome-crm-tool').")

class GeminiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-pro-preview"

    def generate_idea(self):
        """Generates a unique software idea using Gemini 3."""
        prompt = "Generate a creative, unique, and useful software application idea."
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="high"),
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
                thinking_config=types.ThinkingConfig(thinking_level="high"),
                response_mime_type="application/json",
                response_schema=IdeaResponse
            ),
        )
        return json.loads(response.text)
