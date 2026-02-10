"""Core workflow for idea-to-repository automation."""

from typing import Optional, Any

from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from src.core.readme_builder import build_readme
from src.core.models import WorkflowResult
from src.utils.polling import poll_until
from src.core.events import (
    EventBus,
    WorkflowStarted,
    StepStarted,
    StepCompleted,
    RepoCreated,
    ScaffoldGenerated,
    SessionCreated,
    WorkflowCompleted,
    WorkflowFailed,
    LocalEventBus
)


class IdeaWorkflow:
    """Orchestrates the creation of a GitHub repo and Jules session.

    Follows Dependency Injection pattern for testability.
    """

    def __init__(
        self,
        github: Optional[GitHubClient] = None,
        gemini: Optional[GeminiClient] = None,
        jules: Optional[JulesClient] = None,
        event_bus: Optional[EventBus] = None
    ):
        """Initialize workflow with optional service instances.

        Args:
            github: GitHubClient instance (created if None)
            gemini: GeminiClient instance (created if None)
            jules: JulesClient instance (created if None)
            event_bus: EventBus instance (created LocalEventBus if None)
        """
        self.github = github or GitHubClient()
        self.gemini = gemini or GeminiClient()
        self.jules = jules or JulesClient()
        self.event_bus = event_bus or LocalEventBus()

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
            verbose: Print progress messages (Deprecated: use event listeners)

        Returns:
            WorkflowResult with repo_url, session info, etc.
        """
        try:
            self.event_bus.publish(WorkflowStarted(payload=idea_data))

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

            self.event_bus.publish(
                WorkflowCompleted(payload={"result": result.model_dump()})
            )

            return result

        except Exception as e:
            self.event_bus.publish(WorkflowFailed(payload={"error": str(e)}))
            raise e

    def _create_repository(
        self, idea_data: dict[str, Any], private: bool
    ) -> str:
        """Create GitHub repository and return username."""
        user = self.github.get_user()
        username = str(user['login'])

        visibility = "private" if private else "public"
        self.event_bus.publish(StepStarted(payload={
            "name": "create_repo",
            "message": (
                f"Creating {visibility} GitHub repository "
                f"'{idea_data['slug']}'..."
            )
        }))

        self.github.create_repo(
            name=idea_data['slug'],
            description=idea_data['description'][:350],
            private=private
        )

        self.event_bus.publish(RepoCreated(payload={
            "username": username,
            "repo": idea_data['slug'],
            "url": f"https://github.com/{username}/{idea_data['slug']}"
        }))

        self.event_bus.publish(StepCompleted(payload={
            "name": "create_repo",
            "message": "Repository created successfully"
        }))

        return username

    def _generate_scaffold(
        self, username: str, idea_data: dict[str, Any]
    ) -> None:
        """Generate MVP scaffold and commit to repository."""
        self.event_bus.publish(StepStarted(payload={
            "name": "generate_scaffold",
            "message": (
                "Generating MVP scaffold with Gemini "
                "(this may take a moment)..."
            )
        }))

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

        self.event_bus.publish(StepCompleted(payload={
            "name": "generate_scaffold",
            "message": "Scaffold generated",
            "details": "Initializing repository..."
        }))

        # First commit: README
        self.event_bus.publish(StepStarted(payload={
            "name": "commit_files",
            "message": "Initializing repository with README..."
        }))

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
            self.event_bus.publish(StepStarted(payload={
                "name": "commit_scaffold",
                "message": f"Adding {len(files_to_create)} MVP files..."
            }))

            result = self.github.create_files(
                owner=username,
                repo=idea_data['slug'],
                files=files_to_create,
                message="feat: Add MVP scaffold with SOLID structure"
            )

            self.event_bus.publish(ScaffoldGenerated(payload={
                "files_count": len(files_to_create),
                "commit_sha": result.get("commit_sha")
            }))

            self.event_bus.publish(StepCompleted(payload={
                "name": "commit_scaffold",
                "message": (
                    f"Created {result['files_created']} files in single commit"
                )
            }))
        else:
            self.event_bus.publish(StepCompleted(payload={
                "name": "commit_files",
                "message": "README created"
            }))

    def _prepare_scaffold_files(
        self, scaffold: dict[str, Any]
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

        self.event_bus.publish(StepStarted(payload={
            "name": "wait_indexing",
            "message": (
                f"Waiting for Jules to discover the new repository "
                f"(timeout: {timeout}s)..."
            )
        }))

        # Poll for source
        def on_poll(elapsed: int) -> None:
            # We could publish periodic events here
            pass

        source_found = poll_until(
            condition=lambda: self.jules.source_exists(source_id),
            timeout=timeout,
            interval=10,
            on_poll=on_poll
        )

        if not source_found:
            msg = (
                f"WARNING: Source '{source_id}' was not found in Jules "
                f"after {timeout}s."
            )
            self.event_bus.publish(StepCompleted(payload={
                "name": "wait_indexing",
                "message": msg,
                "details": (
                    "Please visit https://jules.google.com to install the app."
                )
            }))
            return None

        self.event_bus.publish(StepCompleted(payload={
            "name": "wait_indexing",
            "message": "Source found!"
        }))

        self.event_bus.publish(StepStarted(payload={
            "name": "create_session",
            "message": "Creating session in Jules..."
        }))

        session = self.jules.create_session(
            source_id, idea_data['description']
        )

        if session:
            self.event_bus.publish(SessionCreated(payload=session))

        self.event_bus.publish(StepCompleted(payload={
            "name": "create_session",
            "message": "Session created successfully"
        }))

        return session
