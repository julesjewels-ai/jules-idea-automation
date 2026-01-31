"""Pydantic models for the Jules Automation Tool."""

from pydantic import BaseModel, Field
from typing import Optional


class TextContentInput(BaseModel):
    """Input model for text content validation."""
    content: str = Field(
        min_length=10,
        max_length=100_000,
        description="The text content to process."
    )


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


class WorkflowResult(BaseModel):
    """Result of the idea-to-repository workflow."""
    idea: IdeaResponse
    repo_url: str
    session_id: Optional[str] = None
    session_url: Optional[str] = None
    pr_url: Optional[str] = None
