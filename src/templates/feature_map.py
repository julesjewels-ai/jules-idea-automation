"""Renders MVP and Production feature map skill files.

When AI-generated FeatureItem data is available the renderers produce
project-specific checklists.  When the Gemini call fails or returns
empty data, the renderers fall back to lightweight static defaults so
every generated repo still ships useful skills.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _tech_stack_str(idea: dict[str, Any]) -> str:
    return ", ".join(idea.get("tech_stack", [])) or "Not specified"


def _render_feature_items(items: list[dict[str, Any]]) -> str:
    """Render a list of FeatureItem dicts to markdown checklist lines."""
    lines: list[str] = []
    for item in items:
        priority = item.get("priority", "P1")
        name = item.get("name", "Unnamed")
        desc = item.get("description", "")
        acceptance = item.get("acceptance", [])
        affected = item.get("affected_files", [])

        lines.append(f"- [ ] **{priority}** — **{name}**")
        if desc:
            lines.append(f"  - *What*: {desc}")
        if acceptance:
            for ac in acceptance:
                lines.append(f"  - *Accept*: {ac}")
        if affected:
            files_str = ", ".join(f"`{f}`" for f in affected)
            lines.append(f"  - *Files*: {files_str}")
        lines.append("")  # blank line between items
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Static fallbacks (used when AI generation fails or returns empty)
# ---------------------------------------------------------------------------


def _static_mvp_items(idea: dict[str, Any]) -> str:
    """Lightweight static MVP checklist derived from idea_data features."""
    features = idea.get("features", []) or ["Core functionality"]
    lines: list[str] = []

    # Feature items
    for i, feat in enumerate(features):
        priority = "P0" if i < max(1, len(features) // 2) else "P1"
        lines.append(f"- [ ] **{priority}** — **{feat}**")
        lines.append("  - *Accept*: Feature is implemented, tested, and documented.")
        lines.append("")

    # Baseline items
    lines.append("- [ ] **P0** — **Environment setup**")
    lines.append("  - *Accept*: `make install && make run` works on a clean checkout.")
    lines.append("")
    lines.append("- [ ] **P1** — **Basic tests**")
    lines.append("  - *Accept*: `make test` passes with ≥ 1 meaningful test per feature.")
    lines.append("")
    lines.append("- [ ] **P1** — **README with demo instructions**")
    lines.append("  - *Accept*: A new developer can clone and demo in < 5 minutes.")
    lines.append("")
    return "\n".join(lines)


def _static_production_items() -> str:
    """Generic production checklist for when AI generation is unavailable."""
    return """- [ ] **P0** — **Structured logging** (replace print statements)
- [ ] **P0** — **Error handling with graceful degradation**
- [ ] **P0** — **Environment-based configuration** (no hardcoded secrets)
- [ ] **P0** — **Docker containerization**
- [ ] **P0** — **Health check endpoint** (if applicable)

- [ ] **P1** — **GitHub Actions CI workflow** (lint + test on push)
- [ ] **P1** — **Input validation and sanitization**
- [ ] **P1** — **Unit test coverage ≥ 80%**
- [ ] **P1** — **Integration tests for critical paths**
- [ ] **P1** — **Dependency pinning** (requirements.txt or lockfile)
- [ ] **P1** — **Rate limiting** (if applicable)
- [ ] **P1** — **API documentation** (if applicable)

- [ ] **P2** — **Database migrations** (if applicable)
- [ ] **P2** — **Monitoring and alerting**
- [ ] **P2** — **Performance profiling**
- [ ] **P2** — **Load testing**
- [ ] **P2** — **Contributing guide**
- [ ] **P2** — **Architecture decision records**
"""


# ---------------------------------------------------------------------------
# Public renderers
# ---------------------------------------------------------------------------


def render_mvp_skill_md(idea: dict[str, Any]) -> str:
    """MVP SKILL.md — agent instructions (does not change with AI data)."""
    title = idea.get("title", "Untitled Project")
    desc = idea.get("description", "No description provided.")
    tech = _tech_stack_str(idea)

    return f"""---
name: mvp-feature-map
description: MVP feature backlog and build checklist for {title}. Use when picking up features, planning sprints, or auditing what's missing.
---

# MVP Feature Map — {title}

> {desc}

**Tech Stack:** {tech}

## How To Use This Skill

1. Open `CHECKLIST.md` in this directory for the prioritized feature backlog.
2. Pick the highest-priority unchecked `[ ]` item.
3. Implement it, write tests, then mark it `[x]`.
4. Repeat until all P0 and P1 items are complete — that's your working prototype.
"""


def render_mvp_checklist_md(
    idea: dict[str, Any],
    ai_items: list[dict[str, Any]] | None = None,
) -> str:
    """MVP CHECKLIST.md — project-specific if AI data available, else static."""
    title = idea.get("title", "Untitled Project")
    slug = idea.get("slug", "project")
    tech = _tech_stack_str(idea)

    if ai_items:
        items_md = _render_feature_items(ai_items)
    else:
        items_md = _static_mvp_items(idea)

    return f"""# MVP Checklist — {title}

> `{slug}` · {tech}

## Features

{items_md}

---
*Generated by jules-idea-automation. Items reference actual project files when available.*
"""


def render_production_skill_md(idea: dict[str, Any]) -> str:
    """Production SKILL.md — agent instructions (does not change with AI data)."""
    title = idea.get("title", "Untitled Project")
    desc = idea.get("description", "No description provided.")
    tech = _tech_stack_str(idea)

    return f"""---
name: production-feature-map
description: Production readiness backlog for {title}. Use when hardening, scaling, or preparing for deployment.
---

# Production Feature Map — {title}

> {desc}

**Tech Stack:** {tech}

## How To Use This Skill

1. Open `CHECKLIST.md` in this directory for the production hardening backlog.
2. Items are prioritized P0 (blocks deployment) → P3 (nice-to-have).
3. Work through P0 items first — these are non-negotiable for production.
4. Skip items explicitly marked as not applicable to your project type.
"""


def render_production_checklist_md(
    idea: dict[str, Any],
    ai_items: list[dict[str, Any]] | None = None,
) -> str:
    """Production CHECKLIST.md — project-specific if AI data available, else static."""
    title = idea.get("title", "Untitled Project")
    slug = idea.get("slug", "project")
    tech = _tech_stack_str(idea)

    if ai_items:
        items_md = _render_feature_items(ai_items)
    else:
        items_md = _static_production_items()

    return f"""# Production Readiness Checklist — {title}

> `{slug}` · {tech}

## Infrastructure & Hardening

{items_md}

---
*Generated by jules-idea-automation. Items reference actual project files when available.*
"""
