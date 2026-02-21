"""Core workflow for idea-to-repository automation."""

from __future__ import annotations

import logging
from typing import Optional, Any

from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from src.core.readme_builder import build_readme
from src.core.models import WorkflowResult, IdeaResponse
from src.core.interfaces import EventBus
from src.core.bus import LocalEventBus
from src.core.events import (
    WorkflowStarted,
    RepoCreated,
    ScaffoldGenerated,
    SessionWaitStarted,
    SessionCreated,
    WorkflowCompleted,
    WorkflowFailed,
    StepStarted
)
from src.utils.polling import poll_until

logger = logging.getLogger(__name__)


class IdeaWorkflow:
    """Orchestrates the creation of a GitHub repo and Jules session from an idea.

    Follows Dependency Injection pattern for testability.
    """

    def __init__(
        self,
        github: Optional[GitHubClient] = None,
        gemini: Optional[GeminiClient] = None,
        jules: Optional[JulesClient] = None,
        bus: Optional[EventBus] = None
    ):
        """Initialize workflow with optional service instances.

        Args:
            github: GitHubClient instance (created if None)
            gemini: GeminiClient instance (created if None)
            jules: JulesClient instance (created if None)
            bus: EventBus instance (created if None)
        """
        self.github = github or GitHubClient()
        self.gemini = gemini or GeminiClient()
        self.jules = jules or JulesClient()
        self.bus = bus or LocalEventBus()

    def execute(
        self,
        idea_data: dict[str, Any],
        private: bool = True,
        timeout: int = 1800,
        verbose: bool = True
    ) -> WorkflowResult:
        """Execute the full workflow.

        Args:
            idea_data: Dict with title, description, slug, tech_stack, features
            private: Create private repository (default: private)
            timeout: Max seconds to wait for Jules indexing
            verbose: Deprecated. Use EventBus for reporting.

        Returns:
            WorkflowResult with repo_url, session info, etc.
        """
        try:
            self.bus.publish(WorkflowStarted(idea=IdeaResponse(**idea_data)))

            # Step 1: Create GitHub repository
            username = self._create_repository(idea_data, private)
            repo_url = f"https://github.com/{username}/{idea_data['slug']}"

            self.bus.publish(RepoCreated(
                username=username,
                slug=idea_data['slug'],
                repo_url=repo_url
            ))

            # Step 2: Generate and commit scaffold
            self._generate_scaffold(username, idea_data)

            # Step 3: Wait for Jules indexing and create session
            session = self._create_jules_session(username, idea_data, timeout)

            if session:
                self.bus.publish(SessionCreated(
                    session_id=session['id'],
                    session_url=session['url']
                ))

            # Build result
            result = WorkflowResult(
                idea=IdeaResponse(**idea_data),
                repo_url=repo_url,
                session_id=session.get('id') if session else None,
                session_url=session.get('url') if session else None
            )

            self.bus.publish(WorkflowCompleted(result=result))

            return result

        except Exception as e:
            self.bus.publish(WorkflowFailed(error=str(e)))
            raise

    def _create_repository(self, idea_data: dict[str, Any], private: bool) -> str:
        """Create GitHub repository and return username."""
        user = self.github.get_user()
        username = str(user['login'])

        visibility = "private" if private else "public"
        self.bus.publish(StepStarted(
            step_name="create_repo",
            description=f"Creating {visibility} GitHub repository '{idea_data['slug']}'"
        ))

        self.github.create_repo(
            name=idea_data['slug'],
            description=idea_data['description'][:350],
            private=private
        )

        return username

    def _generate_scaffold(self, username: str, idea_data: dict[str, Any]) -> None:
        """Generate MVP scaffold and commit to repository."""
        self.bus.publish(StepStarted(
            step_name="generate_scaffold",
            description="Generating MVP scaffold with Gemini"
        ))

        scaffold = self.gemini.generate_project_scaffold(idea_data)

        # Build README
        readme_content = build_readme(
            title=idea_data['title'],
            description=idea_data['description'],
            tech_stack=idea_data.get('tech_stack'),
            features=idea_data.get('features'),
            requirements=scaffold.get('requirements'),
            run_command=scaffold.get('run_command')
        )

        # First commit: README
        self.bus.publish(StepStarted(
            step_name="commit_readme",
            description="Initializing repository with README"
        ))

        self.github.create_file(
            owner=username,
            repo=idea_data['slug'],
            path="README.md",
            content=readme_content,
            message="Initial commit: Add README with project description"
        )

        # Second commit: Scaffold files
        files_to_create = self._prepare_scaffold_files(scaffold)

        if files_to_create:
            self.bus.publish(StepStarted(
                step_name="commit_files",
                description=f"Adding {len(files_to_create)} MVP files"
            ))

            result = self.github.create_files(
                owner=username,
                repo=idea_data['slug'],
                files=files_to_create,
                message="feat: Add MVP scaffold with SOLID structure"
            )

            self.bus.publish(ScaffoldGenerated(files_count=result['files_created']))

    def _prepare_scaffold_files(self, scaffold: dict[str, Any]) -> list[dict[str, str]]:
        """Prepare list of files to create from scaffold data."""
        files_to_create: list[dict[str, str]] = []

        if not scaffold.get('files'):
            return files_to_create

        if not isinstance(scaffold['files'], list):
            logger.warning("Scaffold 'files' is not a list, skipping file creation.")
            return files_to_create

        for file_info in scaffold['files']:
            if not isinstance(file_info, dict) or 'path' not in file_info:
                logger.warning(f"Skipping malformed file entry: {type(file_info)}")
                continue
            if file_info['path'].lower() == 'readme.md':
                continue
            files_to_create.append({
                'path': file_info['path'],
                'content': file_info.get('content', '')
            })

        if scaffold.get('requirements'):
            files_to_create.append({
                'path': 'requirements.txt',
                'content': '\n'.join(scaffold['requirements'])
            })

        return files_to_create

    def _create_jules_session(
        self,
        username: str,
        idea_data: dict[str, Any],
        timeout: int
    ) -> Optional[dict[str, Any]]:
        """Wait for Jules indexing and create session."""
        source_id = f"sources/github/{username}/{idea_data['slug']}"

        self.bus.publish(SessionWaitStarted(
            source_id=source_id,
            timeout=timeout
        ))

        # Poll for source
        def on_poll(elapsed: int) -> None:
            # We could emit a progress event here if desired
            pass

        source_found = poll_until(
            condition=lambda: self.jules.source_exists(source_id),
            timeout=timeout,
            interval=10,
            on_poll=on_poll
        )

        if not source_found:
            # Maybe emit SessionWaitTimeout?
            # For now, just logging error logic handled by reporter if needed?
            # Or assume WorkflowFailed if we raised an exception?
            # The original code returned None and printed a warning.

            # We can log a warning via bus?
            # But for now, let's just return None as before.
            # The caller will finish workflow with session_id=None.
            return None

        return self.jules.create_session(source_id, idea_data['description'])
