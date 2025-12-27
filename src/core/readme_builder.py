"""README file generation utilities."""

from typing import Optional


def build_readme(
    title: str,
    description: str,
    tech_stack: Optional[list[str]] = None,
    features: Optional[list[str]] = None,
    requirements: Optional[list[str]] = None,
    run_command: Optional[str] = None
) -> str:
    """Builds a README.md content string.
    
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
    
    return "\n".join(lines)
