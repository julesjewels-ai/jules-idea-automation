"""README file generation utilities."""

from __future__ import annotations

from typing import Optional


def build_readme(
    title: str,
    description: str,
    tech_stack: Optional[list[str]] = None,
    features: Optional[list[str]] = None,
    requirements: Optional[list[str]] = None,
    run_command: Optional[str] = None
) -> str:
    """Build a README.md content string.
    
    Args:
        title: Project title
        description: Project description
        tech_stack: List of technologies
        features: List of MVP features
        requirements: List of pip dependencies
        run_command: Command to run the application
    
    Returns:
        Complete README.md content as string
    """
    lines = [
        f"# {title}",
        "",
        description,
        "",
    ]
    
    if tech_stack:
        lines.extend([
            "## Tech Stack",
            "",
            *[f"- {tech}" for tech in tech_stack],
            "",
        ])
    
    if features:
        lines.extend([
            "## Features",
            "",
            *[f"- {feature}" for feature in features],
            "",
        ])
    
    # Quick Start section
    lines.extend([
        "## Quick Start",
        "",
        "```bash",
        "# Clone and setup",
        "git clone <repo-url>",
        f"cd {title.lower().replace(' ', '-')}",
        "make install",
        "",
        "# Run the application",
        "make run",
        "```",
        "",
    ])
    
    if requirements:
        lines.extend([
            "## Setup",
            "",
            "```bash",
            "pip install -r requirements.txt",
            "```",
            "",
        ])
    
    if run_command:
        lines.extend([
            "## Usage",
            "",
            "```bash",
            run_command,
            "```",
            "",
        ])
    
    # Development section
    lines.extend([
        "## Development",
        "",
        "```bash",
        "make install  # Create venv and install dependencies",
        "make run      # Run the application",
        "make test     # Run tests",
        "make clean    # Remove cache files",
        "```",
        "",
    ])
    
    # Testing section
    lines.extend([
        "## Testing",
        "",
        "```bash",
        "pytest tests/ -v",
        "```",
        "",
    ])
    
    return "\n".join(lines)

