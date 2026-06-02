"""Tests for the feature map renderers (MVP + Production).

Covers three scenarios:
1. AI-generated items → project-specific checklists
2. No AI items (None) → static fallback checklists
3. Integration: _build_feature_map_files wiring
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
from typing import Any

from src.templates.feature_map import (
    render_mvp_checklist_md,
    render_mvp_skill_md,
    render_production_checklist_md,
    render_production_skill_md,
)

SAMPLE_IDEA: dict[str, Any] = {
    "title": "CodePulse",
    "description": "A developer productivity tracker.",
    "slug": "code-pulse",
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
    "features": ["Session tracking", "Analytics dashboard", "VS Code extension"],
}

SAMPLE_AI_MVP_ITEMS: list[dict[str, Any]] = [
    {
        "priority": "P0",
        "name": "Implement session recording in main.py",
        "description": "Add start/stop session commands to `main.py` using argparse subcommands.",
        "acceptance": [
            "`python main.py start` begins recording.",
            "`python main.py stop` saves the session to the database.",
        ],
        "affected_files": ["main.py", "src/core/app.py"],
    },
    {
        "priority": "P1",
        "name": "Add PostgreSQL persistence",
        "description": "Create SQLAlchemy models in `src/core/models.py` for sessions.",
        "acceptance": ["Sessions are persisted across restarts."],
        "affected_files": ["src/core/models.py", "src/core/app.py"],
    },
]

SAMPLE_AI_PROD_ITEMS: list[dict[str, Any]] = [
    {
        "priority": "P0",
        "name": "Structured logging with structlog",
        "description": "Replace print() calls in `src/core/app.py` with structured JSON logging.",
        "acceptance": ["All log output is valid JSON with level, timestamp, and context."],
        "affected_files": ["src/core/app.py", "main.py"],
    },
    {
        "priority": "P1",
        "name": "Docker multi-stage build",
        "description": "Add Dockerfile with multi-stage build for minimal production image.",
        "acceptance": ["`docker build .` succeeds.", "Image size < 200MB."],
        "affected_files": ["Dockerfile", ".dockerignore"],
    },
]

MINIMAL_IDEA: dict[str, Any] = {"title": "X", "slug": "x"}


# ---------------------------------------------------------------------------
# MVP SKILL.md — always the same shape
# ---------------------------------------------------------------------------


class TestMvpSkillMd:
    def test_contains_project_title(self) -> None:
        assert "CodePulse" in render_mvp_skill_md(SAMPLE_IDEA)

    def test_contains_tech_stack(self) -> None:
        result = render_mvp_skill_md(SAMPLE_IDEA)
        assert "FastAPI" in result

    def test_has_yaml_frontmatter(self) -> None:
        result = render_mvp_skill_md(SAMPLE_IDEA)
        assert result.startswith("---")

    def test_minimal_data_no_crash(self) -> None:
        result = render_mvp_skill_md(MINIMAL_IDEA)
        assert "X" in result


# ---------------------------------------------------------------------------
# MVP CHECKLIST.md — AI items vs. static fallback
# ---------------------------------------------------------------------------


class TestMvpChecklistWithAiItems:
    """When AI-generated items are provided."""

    def test_contains_ai_feature_name(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, SAMPLE_AI_MVP_ITEMS)
        assert "Implement session recording in main.py" in result

    def test_contains_acceptance_criteria(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, SAMPLE_AI_MVP_ITEMS)
        assert "`python main.py start`" in result

    def test_contains_affected_files(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, SAMPLE_AI_MVP_ITEMS)
        assert "`main.py`" in result

    def test_items_are_unchecked(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, SAMPLE_AI_MVP_ITEMS)
        assert "- [ ]" in result
        assert "- [x]" not in result

    def test_priority_labels_present(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, SAMPLE_AI_MVP_ITEMS)
        assert "**P0**" in result
        assert "**P1**" in result


class TestMvpChecklistStaticFallback:
    """When no AI items are available (None)."""

    def test_contains_feature_names(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, None)
        assert "Session tracking" in result

    def test_contains_baseline_items(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, None)
        assert "Environment setup" in result
        assert "Basic tests" in result

    def test_empty_list_also_triggers_fallback(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, [])
        # Empty list is falsy, so should get static fallback
        assert "Session tracking" in result

    def test_template_notice_present(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, None)
        assert "TEMPLATE" in result

    def test_template_notice_absent_with_ai_items(self) -> None:
        result = render_mvp_checklist_md(SAMPLE_IDEA, SAMPLE_AI_MVP_ITEMS)
        assert "TEMPLATE" not in result


# ---------------------------------------------------------------------------
# Production SKILL.md
# ---------------------------------------------------------------------------


class TestProductionSkillMd:
    def test_contains_project_title(self) -> None:
        assert "CodePulse" in render_production_skill_md(SAMPLE_IDEA)

    def test_has_yaml_frontmatter(self) -> None:
        result = render_production_skill_md(SAMPLE_IDEA)
        assert result.startswith("---")


# ---------------------------------------------------------------------------
# Production CHECKLIST.md — AI items vs. static fallback
# ---------------------------------------------------------------------------


class TestProductionChecklistWithAiItems:
    """When AI-generated items are provided."""

    def test_contains_ai_item_name(self) -> None:
        result = render_production_checklist_md(SAMPLE_IDEA, SAMPLE_AI_PROD_ITEMS)
        assert "Structured logging with structlog" in result

    def test_contains_file_references(self) -> None:
        result = render_production_checklist_md(SAMPLE_IDEA, SAMPLE_AI_PROD_ITEMS)
        assert "`Dockerfile`" in result

    def test_contains_acceptance(self) -> None:
        result = render_production_checklist_md(SAMPLE_IDEA, SAMPLE_AI_PROD_ITEMS)
        assert "Image size < 200MB" in result


class TestProductionChecklistStaticFallback:
    """When no AI items are available."""

    def test_contains_generic_items(self) -> None:
        result = render_production_checklist_md(SAMPLE_IDEA, None)
        assert "Structured logging" in result
        assert "Docker containerization" in result

    def test_all_items_unchecked(self) -> None:
        result = render_production_checklist_md(SAMPLE_IDEA, None)
        assert "- [x]" not in result

    def test_template_notice_present(self) -> None:
        result = render_production_checklist_md(SAMPLE_IDEA, None)
        assert "TEMPLATE" in result

    def test_template_notice_absent_with_ai_items(self) -> None:
        result = render_production_checklist_md(SAMPLE_IDEA, SAMPLE_AI_PROD_ITEMS)
        assert "TEMPLATE" not in result

    def test_api_items_present_for_fastapi_stack(self) -> None:
        """SAMPLE_IDEA uses FastAPI, so API-specific items should appear."""
        result = render_production_checklist_md(SAMPLE_IDEA, None)
        assert "Health check endpoint" in result
        assert "Rate limiting" in result

    def test_db_items_present_for_postgresql_stack(self) -> None:
        """SAMPLE_IDEA uses PostgreSQL, so DB migration item should appear."""
        result = render_production_checklist_md(SAMPLE_IDEA, None)
        assert "Database migrations" in result

    def test_api_items_absent_for_non_api_stack(self) -> None:
        """A project without API frameworks should skip API-specific items."""
        idea_no_api = {"title": "CLI Tool", "slug": "cli-tool", "tech_stack": ["Python", "Click"]}
        result = render_production_checklist_md(idea_no_api, None)
        assert "Health check endpoint" not in result
        assert "Rate limiting" not in result

    def test_db_items_absent_for_non_db_stack(self) -> None:
        """A project without DB tech should skip DB-specific items."""
        idea_no_db = {"title": "CLI Tool", "slug": "cli-tool", "tech_stack": ["Python", "Click"]}
        result = render_production_checklist_md(idea_no_db, None)
        assert "Database migrations" not in result


# ---------------------------------------------------------------------------
# _build_feature_map_files integration
# ---------------------------------------------------------------------------


class TestBuildFeatureMapFiles:
    """Test the workflow helper that stitches everything together."""

    def test_returns_four_files_with_ai_data(self) -> None:
        from src.core.workflow import _build_feature_map_files

        feature_maps = {
            "mvp_features": SAMPLE_AI_MVP_ITEMS,
            "production_features": SAMPLE_AI_PROD_ITEMS,
        }
        files = _build_feature_map_files(SAMPLE_IDEA, feature_maps)
        assert len(files) == 4

    def test_ai_items_appear_in_checklist_content(self) -> None:
        from src.core.workflow import _build_feature_map_files

        feature_maps = {
            "mvp_features": SAMPLE_AI_MVP_ITEMS,
            "production_features": SAMPLE_AI_PROD_ITEMS,
        }
        files = _build_feature_map_files(SAMPLE_IDEA, feature_maps)
        contents = {f["path"]: f["content"] for f in files}

        assert "Implement session recording" in contents[".agent/skills/mvp-feature-map/CHECKLIST.md"]
        assert "Structured logging with structlog" in contents[".agent/skills/production-feature-map/CHECKLIST.md"]

    def test_returns_four_files_without_ai_data(self) -> None:
        from src.core.workflow import _build_feature_map_files

        files = _build_feature_map_files(SAMPLE_IDEA, None)
        assert len(files) == 4

    def test_static_fallback_in_content_without_ai_data(self) -> None:
        from src.core.workflow import _build_feature_map_files

        files = _build_feature_map_files(SAMPLE_IDEA, None)
        contents = {f["path"]: f["content"] for f in files}

        # Should contain static MVP items (from idea features)
        assert "Session tracking" in contents[".agent/skills/mvp-feature-map/CHECKLIST.md"]
        # Should contain static production items
        assert "Docker containerization" in contents[".agent/skills/production-feature-map/CHECKLIST.md"]
