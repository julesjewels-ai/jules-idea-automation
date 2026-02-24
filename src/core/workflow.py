"""Core workflow for idea-to-repository automation."""

from __future__ import annotations

import logging
from typing import Optional, Any

from src.services.gemini import GeminiClient
from src.services.github import GitHubClient
from src.services.jules import JulesClient
from src.core.readme_builder import build_readme
from src.core.models import WorkflowResult
from src.utils.polling import poll_until
from src.utils.reporter import print_workflow_report

logger = logging.getLogger(__name__)


class IdeaWorkflow:
    """Orchestrates the creation of a GitHub repo and Jules session from an idea.
    
    Follows Dependency Injection pattern for testability.
    """
    
    def __init__(
        self,
        github: Optional[GitHubClient] = None,
        gemini: Optional[GeminiClient] = None,
        jules: Optional[JulesClient] = None
    ):
        """Initialize workflow with optional service instances.
        
        Args:
            github: GitHubClient instance (created if None)
            gemini: GeminiClient instance (created if None)
            jules: JulesClient instance (created if None)
        """
        self.github = github or GitHubClient()
        self.gemini = gemini or GeminiClient()
        self.jules = jules or JulesClient()
    
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
            verbose: Print progress messages
        
        Returns:
            WorkflowResult with repo_url, session info, etc.
        """
        if verbose:
            print(f"Processing Idea: {idea_data['title']}")
            print(f"Slug: {idea_data['slug']}")
            print("-" * 40)
        
        # Step 1: Create GitHub repository
        username = self._create_repository(idea_data, private, verbose)
        repo_url = f"https://github.com/{username}/{idea_data['slug']}"
        
        # Step 2: Generate and commit scaffold
        self._generate_scaffold(username, idea_data, verbose)
        
        # Step 3: Wait for Jules indexing and create session
        session = self._create_jules_session(username, idea_data, timeout, verbose)
        
        # Build result
        from src.core.models import IdeaResponse
        result = WorkflowResult(
            idea=IdeaResponse(**idea_data),
            repo_url=repo_url,
            session_id=session.get('id') if session else None,
            session_url=session.get('url') if session else None
        )
        
        if verbose:
            print_workflow_report(
                title=idea_data['title'],
                slug=idea_data['slug'],
                repo_url=repo_url,
                session_id=result.session_id,
                session_url=result.session_url
            )
        
        return result
    
    def _create_repository(self, idea_data: dict[str, Any], private: bool, verbose: bool) -> str:
        """Create GitHub repository and return username."""
        user = self.github.get_user()
        username = str(user['login'])
        
        visibility = "private" if private else "public"
        if verbose:
            print(f"Creating {visibility} GitHub repository '{idea_data['slug']}'...")
        
        self.github.create_repo(
            name=idea_data['slug'],
            description=idea_data['description'][:350],
            private=private
        )
        
        return username
    
    def _generate_scaffold(self, username: str, idea_data: dict[str, Any], verbose: bool) -> None:
        """Generate MVP scaffold and commit to repository."""
        if verbose:
            print("Generating MVP scaffold with Gemini (this may take a moment)...")
        
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
        if verbose:
            print("Initializing repository with README...")
        
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
            if verbose:
                print(f"Adding {len(files_to_create)} MVP files...")
            
            result = self.github.create_files(
                owner=username,
                repo=idea_data['slug'],
                files=files_to_create,
                message="feat: Add MVP scaffold with SOLID structure"
            )
            
            if verbose:
                print(f"  Created {result['files_created']} files in single commit")

    def _process_file_entry(self, file_info: Any) -> Optional[dict[str, str]]:
        """Validate and format a single file entry."""
        if not isinstance(file_info, dict) or 'path' not in file_info:
            logger.warning(f"Skipping malformed file entry: {type(file_info)}")
            return None

        if file_info['path'].lower() == 'readme.md':
            return None

        return {
            'path': file_info['path'],
            'content': file_info.get('content', '')
        }

    def _prepare_scaffold_files(self, scaffold: dict[str, Any]) -> list[dict[str, str]]:
        """Prepare list of files to create from scaffold data."""
        files_to_create: list[dict[str, str]] = []

        files_list = scaffold.get('files')
        if not files_list:
            return files_to_create

        if not isinstance(files_list, list):
            logger.warning("Scaffold 'files' is not a list, skipping file creation.")
            return files_to_create

        for file_info in files_list:
            processed_file = self._process_file_entry(file_info)
            if processed_file:
                files_to_create.append(processed_file)

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
        timeout: int,
        verbose: bool
    ) -> Optional[dict[str, Any]]:
        """Wait for Jules indexing and create session."""
        source_id = f"sources/github/{username}/{idea_data['slug']}"
        
        if verbose:
            print(f"Constructed Source ID: {source_id}")
            print(f"Waiting for Jules to discover the new repository (timeout: {timeout}s)...")
        
        # Poll for source
        def on_poll(elapsed: int) -> None:
            if verbose:
                print(f"  Source not yet indexed ({elapsed}s elapsed)...")
        
        source_found = poll_until(
            condition=lambda: self.jules.source_exists(source_id),
            timeout=timeout,
            interval=10,
            on_poll=on_poll
        )
        
        if not source_found:
            if verbose:
                print(f"WARNING: Source '{source_id}' was not found in Jules after {timeout}s.")
                print("Please visit https://jules.google.com to install the app.")
            return None
        
        if verbose:
            print("Source found! Creating session in Jules...")
        
        return self.jules.create_session(source_id, idea_data['description'])
