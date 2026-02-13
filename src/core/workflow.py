"""Core workflow for idea-to-repository automation."""

from typing import Optional, Any

from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from src.core.readme_builder import build_readme
from src.core.models import WorkflowResult
from src.core.events import (
    EventBus,
    WorkflowStarted,
    StepStarted,
    StepCompleted,
    WorkflowCompleted,
    WorkflowFailed
)
from src.services.bus import LocalEventBus
from src.utils.polling import poll_until


class IdeaWorkflow:
    """Orchestrates the creation of a GitHub repo and Jules session.

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
            bus: EventBus instance (creates LocalEventBus if None)
        """
        self.github = github or GitHubClient()
        self.gemini = gemini or GeminiClient()
        self.jules = jules or JulesClient()
        self.bus = bus or LocalEventBus()

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
            verbose: Print progress messages (deprecated, uses EventBus)

        Returns:
            WorkflowResult with repo_url, session info, etc.
        """
        self.bus.publish(
            WorkflowStarted(
                idea_title=idea_data['title'],
                slug=idea_data['slug']))

        try:
            # Step 1: Create GitHub repository
            username = self._create_repository(idea_data, private)
            repo_url = f"https://github.com/{username}/{idea_data['slug']}"

            # Step 2: Generate and commit scaffold
            self._generate_scaffold(username, idea_data)

            # Step 3: Wait for Jules indexing and create session
            session = self._create_jules_session(username, idea_data, timeout)

            # Build result
            from src.core.models import IdeaResponse
            result = WorkflowResult(
                idea=IdeaResponse(**idea_data),
                repo_url=repo_url,
                session_id=session.get('id') if session else None,
                session_url=session.get('url') if session else None
            )

            self.bus.publish(WorkflowCompleted(result=result))

            return result
        except Exception as e:
            self.bus.publish(
                WorkflowFailed(
                    error=str(e),
                    tip="Check logs for more details."))
            raise

    def _create_repository(
            self, idea_data: dict[str, Any], private: bool) -> str:
        """Create GitHub repository and return username."""
        visibility = "private" if private else "public"
        self.bus.publish(
            StepStarted(
                step_name="create_repo",
                message=f"Creating {visibility} GitHub repository '{
                    idea_data['slug']}'..."))

        user = self.github.get_user()
        username = str(user['login'])

        self.github.create_repo(
            name=idea_data['slug'],
            description=idea_data['description'][:350],
            private=private
        )

        self.bus.publish(
            StepCompleted(
                step_name="create_repo",
                message="Repository created"))
        return username

    def _generate_scaffold(self, username: str,
                           idea_data: dict[str, Any]) -> None:
        """Generate MVP scaffold and commit to repository."""
        self.bus.publish(
            StepStarted(
                step_name="generate_scaffold",
                message="Generating MVP scaffold with Gemini..."))

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
        self.bus.publish(
            StepStarted(
                step_name="commit_readme",
                message="Initializing repository with README..."))

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
            self.bus.publish(
                StepStarted(
                    step_name="commit_files",
                    message=f"Adding {
                        len(files_to_create)} MVP files..."))

            result = self.github.create_files(
                owner=username,
                repo=idea_data['slug'],
                files=files_to_create,
                message="feat: Add MVP scaffold with SOLID structure"
            )

            self.bus.publish(
                StepCompleted(
                    step_name="commit_files",
                    message="Scaffold files committed",
                    result=result))

    def _prepare_scaffold_files(
            self, scaffold: dict[str, Any]) -> list[dict[str, str]]:
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

        self.bus.publish(
            StepStarted(
                step_name="wait_for_indexing",
                message=f"Waiting for Jules... (timeout: {timeout}s)"))

        # Poll for source
        def on_poll(elapsed: int) -> None:
            pass

        source_found = poll_until(
            condition=lambda: self.jules.source_exists(source_id),
            timeout=timeout,
            interval=10,
            on_poll=on_poll
        )

        if not source_found:
            self.bus.publish(
                StepCompleted(
                    step_name="wait_for_indexing",
                    message="Source not found"))
            # Ideally we should publish a warning event or include it in the
            # result, but StepCompleted message is sufficient for console
            # reporter
            return None

        self.bus.publish(
            StepStarted(
                step_name="create_session",
                message="Source found! Creating session in Jules..."))

        session = self.jules.create_session(
            source_id, idea_data['description'])
        self.bus.publish(
            StepCompleted(
                step_name="create_session",
                message="Session created"))
        return session
