"""Unit tests for IdeaWorkflow.execute() partial-failure recovery."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.workflow import IdeaWorkflow


def _make_idea_data() -> dict[str, Any]:
    """Minimal valid idea_data fixture."""
    return {
        "title": "Test App",
        "description": "A test application.",
        "slug": "test-app",
        "tech_stack": ["python"],
        "features": ["feature-1"],
    }


def _make_workflow(
    *,
    github: MagicMock | None = None,
    gemini: MagicMock | None = None,
    jules: MagicMock | None = None,
) -> IdeaWorkflow:
    """Create an IdeaWorkflow with fully mocked service clients.

    Default responses are always configured. Callers override specific
    methods (e.g. via ``side_effect``) on their own mock before passing it.
    """
    gh = github if github is not None else MagicMock()
    gm = gemini if gemini is not None else MagicMock()
    jl = jules if jules is not None else MagicMock()

    # Always set baseline defaults — callers override via side_effect
    if not isinstance(gh.get_user.return_value, dict):
        gh.get_user.return_value = {"login": "testuser"}
    if not isinstance(gh.create_repo.return_value, dict):
        gh.create_repo.return_value = {}
    if not isinstance(gh.create_file.return_value, dict):
        gh.create_file.return_value = {}
    if not isinstance(gh.create_files.return_value, dict):
        gh.create_files.return_value = {"files_created": 3}

    if not isinstance(gm.generate_project_scaffold.return_value, dict):
        gm.generate_project_scaffold.return_value = {
            "files": [
                {"path": "main.py", "content": "print('hello')"},
            ],
            "requirements": ["pytest"],
            "run_command": "python main.py",
        }
    if not isinstance(gm.generate_feature_maps.return_value, dict):
        gm.generate_feature_maps.return_value = {
            "mvp_features": [],
            "production_features": [],
        }

    if not isinstance(jl.source_exists.return_value, bool):
        jl.source_exists.return_value = True
    if not isinstance(jl.create_session.return_value, dict):
        jl.create_session.return_value = {
            "id": "session-123",
            "url": "https://jules.google.com/sessions/session-123",
        }

    return IdeaWorkflow(github=gh, gemini=gm, jules=jl)


class TestWorkflowExecute:
    """Tests for IdeaWorkflow.execute() graceful failure recovery."""

    @patch("src.core.workflow.poll_until", return_value=True)
    def test_happy_path(self, _mock_poll: MagicMock) -> None:
        """All services succeed → full WorkflowResult."""
        wf = _make_workflow()
        result = wf.execute(_make_idea_data())

        assert result.repo_url == "https://github.com/testuser/test-app"
        assert result.session_id == "session-123"
        assert result.session_url is not None

    @patch("src.core.workflow.poll_until", return_value=True)
    def test_jules_session_failure_returns_repo_url(self, _mock_poll: MagicMock) -> None:
        """Jules create_session raises → result still has repo_url, session_id=None."""
        jules = MagicMock()
        jules.source_exists.return_value = True
        jules.create_session.side_effect = RuntimeError("Jules API 500")

        wf = _make_workflow(jules=jules)
        result = wf.execute(_make_idea_data())

        assert result.repo_url == "https://github.com/testuser/test-app"
        assert result.session_id is None
        assert result.session_url is None

    @patch("src.core.workflow.poll_until", return_value=True)
    def test_scaffold_failure_still_creates_session(self, _mock_poll: MagicMock) -> None:
        """Scaffold generation raises → repo + Jules session still work."""
        gemini = MagicMock()
        gemini.generate_project_scaffold.side_effect = RuntimeError("Gemini timeout")

        jules = MagicMock()
        jules.source_exists.return_value = True
        jules.create_session.return_value = {
            "id": "session-456",
            "url": "https://jules.google.com/sessions/session-456",
        }

        wf = _make_workflow(gemini=gemini, jules=jules)
        result = wf.execute(_make_idea_data())

        assert result.repo_url == "https://github.com/testuser/test-app"
        assert result.session_id == "session-456"

    def test_repo_creation_failure_propagates(self) -> None:
        """Repo creation failure → exception propagates (nothing to recover)."""
        github = MagicMock()
        github.get_user.return_value = {"login": "testuser"}
        github.create_repo.side_effect = RuntimeError("GitHub 403")

        wf = _make_workflow(github=github)

        with pytest.raises(RuntimeError, match="GitHub 403"):
            wf.execute(_make_idea_data())
