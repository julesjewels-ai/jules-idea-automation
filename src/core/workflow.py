"""Core workflow for idea-to-repository automation."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from src.core.events import WorkflowCompleted, WorkflowStarted
from src.core.interfaces import EventBus
from src.core.models import IdeaResponse, WorkflowResult
from src.core.readme_builder import build_readme
from src.services.bus import NullEventBus
from src.services.cache import FileCacheProvider
from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from src.templates.feature_map import (
    render_mvp_checklist_md,
    render_mvp_skill_md,
    render_production_checklist_md,
    render_production_skill_md,
)
from src.utils.polling import poll_until
from src.utils.reporter import Spinner, format_duration, print_workflow_report

logger = logging.getLogger(__name__)


def _build_feature_map_files(
    idea_data: dict[str, Any],
    feature_maps: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Build the MVP and Production feature map skill files.

    When *feature_maps* is provided (from Gemini) the checklists are
    project-specific.  Otherwise the renderers fall back to static defaults.
    """
    mvp_items = (feature_maps or {}).get("mvp_features") or None
    prod_items = (feature_maps or {}).get("production_features") or None

    return [
        {
            "path": ".agent/skills/mvp-feature-map/SKILL.md",
            "content": render_mvp_skill_md(idea_data),
        },
        {
            "path": ".agent/skills/mvp-feature-map/CHECKLIST.md",
            "content": render_mvp_checklist_md(idea_data, mvp_items),
        },
        {
            "path": ".agent/skills/production-feature-map/SKILL.md",
            "content": render_production_skill_md(idea_data),
        },
        {
            "path": ".agent/skills/production-feature-map/CHECKLIST.md",
            "content": render_production_checklist_md(idea_data, prod_items),
        },
    ]


def _parse_dict_requirement(key: Any, value: Any) -> str:
    """Parse a single dictionary-style requirement mapping."""
    if value and isinstance(value, str) and value.strip() not in ("*", "latest"):
        return f"{key}{value}"
    return str(key)


def _parse_list_dict_requirement(item: dict[str, Any]) -> str:
    """Parse a single requirement object from a list."""
    name = item.get("package") or item.get("name") or ""
    version = item.get("version") or item.get("constraint") or ""
    return f"{name}{version}" if version else str(name)


def _parse_list_requirement(item: Any) -> str:
    """Parse a single requirement item from a list."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return _parse_list_dict_requirement(item)
    return str(item)


def _normalize_requirements(raw: Any) -> list[str]:
    """Normalize requirements from various LLM return formats to a flat list.

    Supported formats:
        - list[str]  (expected): ["pytest", "requests"]
        - dict       (flash fallback): {"pytest": ">=7", "requests": "*"}
        - list[dict] (unusual): [{"package": "pytest", "version": ">=7"}]
        - scalar     (edge case): "pytest"
    """
    if isinstance(raw, dict):
        return [_parse_dict_requirement(k, v) for k, v in raw.items()]

    if isinstance(raw, list):
        return [_parse_list_requirement(item) for item in raw]

    return [str(raw)]


class IdeaWorkflow:
    """Orchestrates the creation of a GitHub repo and Jules session from an idea.

    Follows Dependency Injection pattern for testability.
    """

    def __init__(
        self,
        github: GitHubClient | None = None,
        gemini: GeminiClient | None = None,
        jules: JulesClient | None = None,
        event_bus: EventBus | None = None,
    ):
        """Initialize workflow with optional service instances.

        Args:
        ----
            github: GitHubClient instance (created if None)
            gemini: GeminiClient instance (created if None)
            jules: JulesClient instance (created if None)
            event_bus: EventBus instance (optional)

        """
        self.github = github or GitHubClient()
        self.event_bus = event_bus or NullEventBus()
        self.gemini = gemini or GeminiClient(cache_provider=FileCacheProvider())
        self.jules = jules or JulesClient()

    def execute(self, idea_data: dict[str, Any], private: bool = True, timeout: int = 1800) -> WorkflowResult:
        """Execute the full workflow.

        Args:
        ----
            idea_data: Dict with title, description, slug, tech_stack, features
            private: Create private repository (default: private)
            timeout: Max seconds to wait for Jules indexing

        Returns:
        -------
            WorkflowResult with repo_url, session info, etc.

        """
        logger.debug("Processing Idea: %s", idea_data["title"])
        logger.debug("Slug: %s", idea_data["slug"])

        self.event_bus.publish(
            WorkflowStarted(
                event_id=str(uuid.uuid4()),
                idea_title=idea_data["title"],
                idea_slug=idea_data["slug"],
                category=idea_data.get("category"),
            )
        )

        # Step 1: Create GitHub repository
        username = self._create_repository(idea_data, private)
        repo_url = f"https://github.com/{username}/{idea_data['slug']}"

        # Step 2: Generate and commit scaffold
        self._generate_scaffold(username, idea_data)

        # Step 3: Wait for Jules indexing and create session
        session = self._create_jules_session(username, idea_data, timeout)

        # Build result
        result = WorkflowResult(
            idea=IdeaResponse(**idea_data),
            repo_url=repo_url,
            session_id=session.get("id") if session else None,
            session_url=session.get("url") if session else None,
        )

        print_workflow_report(
            title=idea_data["title"],
            slug=idea_data["slug"],
            repo_url=repo_url,
            session_id=result.session_id,
            session_url=result.session_url,
        )

        self.event_bus.publish(
            WorkflowCompleted(
                event_id=str(uuid.uuid4()),
                idea_title=idea_data["title"],
                idea_slug=idea_data["slug"],
                repo_url=repo_url,
                session_id=result.session_id,
                session_url=result.session_url,
            )
        )

        return result

    def _create_repository(self, idea_data: dict[str, Any], private: bool) -> str:
        """Create GitHub repository and return username."""
        user = self.github.get_user()
        username = str(user["login"])

        visibility = "private" if private else "public"
        logger.debug("Creating %s GitHub repository '%s'...", visibility, idea_data["slug"])

        with Spinner(
            f"Creating {visibility} GitHub repository '{idea_data['slug']}'…",
            success_message=f"Repository created ({visibility})",
        ):
            self.github.create_repo(
                name=idea_data["slug"],
                description=idea_data["description"][:350],
                private=private,
            )

        return username

    def _generate_scaffold(self, username: str, idea_data: dict[str, Any]) -> None:
        """Generate MVP scaffold and commit to repository."""
        with Spinner(
            "Generating MVP scaffold with Gemini…",
            success_message="MVP scaffold generated",
        ):
            scaffold = self.gemini.generate_project_scaffold(idea_data)

        # Build README
        readme_content = build_readme(
            title=idea_data["title"],
            description=idea_data["description"],
            tech_stack=idea_data.get("tech_stack"),
            features=idea_data.get("features"),
            requirements=scaffold.get("requirements"),
            run_command=scaffold.get("run_command"),
        )

        # First commit: README
        with Spinner(
            "Initializing repository with README…",
            success_message="README committed",
        ):
            self.github.create_file(
                owner=username,
                repo=idea_data["slug"],
                path="README.md",
                content=readme_content,
                message="Initial commit: Add README with project description",
            )

        # Second commit: Scaffold files + feature maps
        files_to_create = self._prepare_scaffold_files(scaffold)

        # Generate project-specific feature maps using the scaffold as context
        with Spinner(
            "Generating project-specific feature maps…",
            success_message="Feature maps generated",
        ):
            feature_maps = self.gemini.generate_feature_maps(idea_data, scaffold.get("files", []))
        feature_map_files = _build_feature_map_files(idea_data, feature_maps)
        files_to_create.extend(feature_map_files)

        if files_to_create:
            with Spinner(
                f"Committing {len(files_to_create)} scaffold files…",
                success_message=f"{len(files_to_create)} files committed",
            ):
                result = self.github.create_files(
                    owner=username,
                    repo=idea_data["slug"],
                    files=files_to_create,
                    message="feat: Add MVP scaffold with SOLID structure",
                )

            logger.debug("Created %d files in single commit", result["files_created"])

    def _process_file_entry(self, file_info: Any) -> dict[str, str] | None:
        """Validate and format a single file entry."""
        if not isinstance(file_info, dict) or "path" not in file_info:
            logger.warning("Skipping malformed file entry: %s", type(file_info))
            return None

        if file_info["path"].lower() == "readme.md":
            return None

        return {"path": file_info["path"], "content": file_info.get("content", "")}

    def _prepare_scaffold_files(self, scaffold: dict[str, Any]) -> list[dict[str, str]]:
        """Prepare list of files to create from scaffold data."""
        files_to_create: list[dict[str, str]] = []

        files_list = scaffold.get("files")
        if not files_list:
            return files_to_create

        if not isinstance(files_list, list):
            logger.warning("Scaffold 'files' is not a list, skipping file creation.")
            return files_to_create

        for file_info in files_list:
            processed_file = self._process_file_entry(file_info)
            if processed_file:
                files_to_create.append(processed_file)

        raw_requirements = scaffold.get("requirements")
        if raw_requirements:
            req_lines = _normalize_requirements(raw_requirements)
            files_to_create.append(
                {
                    "path": "requirements.txt",
                    "content": "\n".join(line for line in req_lines if line),
                }
            )

        return files_to_create

    def _create_jules_session(self, username: str, idea_data: dict[str, Any], timeout: int) -> dict[str, Any] | None:
        """Wait for Jules indexing and create session."""
        source_id = f"sources/github/{username}/{idea_data['slug']}"
        logger.debug("Constructed Source ID: %s", source_id)

        with Spinner(
            f"Waiting for Jules to discover repository (timeout: {format_duration(timeout)})…",
        ) as spinner:

            def on_poll(elapsed: int) -> None:
                spinner.update(
                    f"[{format_duration(elapsed)}] Waiting for Jules to index repository…"
                )

            source_found = poll_until(
                condition=lambda: self.jules.source_exists(source_id),
                timeout=timeout,
                interval=10,
                on_poll=on_poll,
            )

        if not source_found:
            logger.warning("Source '%s' was not found in Jules after %ds.", source_id, timeout)
            logger.warning("Please visit https://jules.google.com to install the app.")
            return None

        with Spinner(
            "Creating Jules session…",
            success_message="Jules session created",
        ):
            session = self.jules.create_session(source_id, idea_data["description"])

        return session
