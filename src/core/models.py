"""Pydantic models for the Jules Automation Tool."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path


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
    def _read_template(cls, filename: str) -> str:
        """Read a template file."""
        template_dir = Path(__file__).parent.parent / "templates" / "scaffold"
        template_path = template_dir / filename
        try:
            return template_path.read_text(encoding="utf-8")
        except Exception as e:
            return ""

    @classmethod
    def create_fallback_scaffold(cls, title: str, description: str) -> "ProjectScaffold":
        """Create a default scaffold when generation fails."""
        desc = description[:200]
        
        def render(filename: str) -> str:
            content = cls._read_template(filename)
            # Use replace instead of format because strings like Makefile contain literal curly braces
            return content.replace("{title}", title).replace("{desc}", desc)
            
        return cls(
            files=[
                ProjectFile(path="main.py", content=render("main.py.tpl"), description="Main entry point with CLI"),
                ProjectFile(path="src/__init__.py", content=cls._read_template("src_init.py.tpl"), description="Package marker"),
                ProjectFile(path="src/core/__init__.py", content=cls._read_template("src_core_init.py.tpl"), description="Package marker"),
                ProjectFile(path="src/core/app.py", content=render("src_core_app.py.tpl"), description="Main business logic"),
                ProjectFile(path="Makefile", content=cls._read_template("Makefile.tpl"), description="Development commands"),
                ProjectFile(path=".env.example", content=render("env.example.tpl"), description="Environment template"),
                ProjectFile(path=".gitignore", content=cls._read_template("gitignore.tpl"), description="Git ignore file"),
                ProjectFile(path="tests/__init__.py", content=cls._read_template("tests_init.py.tpl"), description="Test package marker"),
                ProjectFile(path="tests/test_core.py", content=render("tests_test_core.py.tpl"), description="Core unit tests")
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
