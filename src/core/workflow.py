"""Core workflow for idea-to-repository automation."""

from __future__ import annotations

from typing import Optional, Any

from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from src.core.readme_builder import build_readme
from src.core.models import WorkflowResult, IdeaResponse
from src.utils.polling import poll_until
from src.core.interfaces import EventBus
from src.core.events import (
    WorkflowStarted,
    StepStarted,
    StepProgress,
    StepCompleted,
    StepFailed,
    RepoCreated,
    ScaffoldGenerated,
    JulesSessionCreated,
    WorkflowCompleted,
    WorkflowFailed,
)


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
            bus: EventBus instance for publishing events
                (defaults to LocalEventBus if None)
        """
        self.github = github or GitHubClient()
        self.gemini = gemini or GeminiClient()
        self.jules = jules or JulesClient()

        if bus:
            self.bus = bus
        else:
            from src.services.event_bus import LocalEventBus
            self.bus = LocalEventBus()

    def execute(
        self,
        idea_data: dict[str, Any],
        private: bool = False,
        timeout: int = 1800,
        verbose: bool = True
    ) -> WorkflowResult:
        """Execute the full workflow.

        Args:
            idea_data: Dict with title, description, slug, tech_stack, features
            private: Create private repository (default: public)
            timeout: Max seconds to wait for Jules indexing
            verbose: Deprecated. Use EventBus listeners for reporting.

        Returns:
            WorkflowResult with repo_url, session info, etc.
        """
        try:
            idea = IdeaResponse(**idea_data)
            self.bus.publish(WorkflowStarted(idea=idea))

            # Step 1: Create GitHub repository
            repo_desc = f"Creating {'private' if private else 'public'} " \
                        f"GitHub repository '{idea_data['slug']}'..."
            self.bus.publish(StepStarted(
                step_name="create_repo",
                message=repo_desc
            ))
            username = self._create_repository(idea_data, private)
            repo_url = f"https://github.com/{username}/{idea_data['slug']}"
            self.bus.publish(RepoCreated(repo_url=repo_url))
            self.bus.publish(StepCompleted(
                step_name="create_repo", result="Repository created"))

            # Step 2: Generate and commit scaffold
            self.bus.publish(StepStarted(
                step_name="scaffold",
                message="Generating MVP scaffold with Gemini..."
            ))
            self._generate_scaffold(username, idea_data)
            self.bus.publish(StepCompleted(
                step_name="scaffold",
                result="Scaffold generated and pushed"
            ))

            # Step 3: Wait for Jules indexing and create session
            self.bus.publish(StepStarted(
                step_name="jules_session",
                message=f"Waiting for Jules indexing (timeout: {timeout}s)..."
            ))
            session = self._create_jules_session(username, idea_data, timeout)

            if session:
                self.bus.publish(JulesSessionCreated(
                    session_id=session['id'],
                    session_url=session['url']
                ))
                self.bus.publish(StepCompleted(
                    step_name="jules_session",
                    result="Jules session created"
                ))
            else:
                self.bus.publish(StepCompleted(
                    step_name="jules_session",
                    result="Jules session skipped (timeout)"
                ))

            # Build result
            result = WorkflowResult(
                idea=idea,
                repo_url=repo_url,
                session_id=session.get('id') if session else None,
                session_url=session.get('url') if session else None
            )

            self.bus.publish(WorkflowCompleted(result=result))

            return result
        except Exception as e:
            self.bus.publish(WorkflowFailed(error=str(e)))
            raise

    def _create_repository(
        self,
        idea_data: dict[str, Any],
        private: bool
    ) -> str:
        """Create GitHub repository and return username."""
        user = self.github.get_user()
        username = str(user['login'])

        self.github.create_repo(
            name=idea_data['slug'],
            description=idea_data['description'][:350],
            private=private
        )

        return username

    def _generate_scaffold(
        self,
        username: str,
        idea_data: dict[str, Any]
    ) -> None:
        """Generate MVP scaffold and commit to repository."""
        scaffold = self.gemini.generate_project_scaffold(idea_data)

        # Emit scaffold event
        file_count = len(scaffold.get('files', []))
        self.bus.publish(ScaffoldGenerated(file_count=file_count))

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
            self.github.create_files(
                owner=username,
                repo=idea_data['slug'],
                files=files_to_create,
                message="feat: Add MVP scaffold with SOLID structure"
            )

    def _prepare_scaffold_files(
        self,
        scaffold: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Prepare list of files to create from scaffold data."""
        files_to_create: list[dict[str, str]] = []

        if not scaffold.get('files'):
            return files_to_create

        for file_info in scaffold['files']:
            if file_info['path'].lower() == 'readme.md':
                continue
            files_to_create.append({
                'path': file_info['path'],
                'content': file_info['content']
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

        # Poll for source
        def on_poll(elapsed: int) -> None:
            self.bus.publish(StepProgress(
                step_name="jules_session",
                message=f"Waiting for indexing ({elapsed}s elapsed)..."
            ))

        source_found = poll_until(
            condition=lambda: self.jules.source_exists(source_id),
            timeout=timeout,
            interval=10,
            on_poll=on_poll
        )

        if not source_found:
            msg = f"Source '{source_id}' was not found in Jules after {timeout}s."
            self.bus.publish(StepFailed(step_name="jules_session", error=msg))
            return None

        return self.jules.create_session(source_id, idea_data['description'])
