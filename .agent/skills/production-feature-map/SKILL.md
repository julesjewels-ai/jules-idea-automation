---
name: production-feature-map
description: Comprehensive production readiness backlog for the jules-idea-automation CLI tool AND the repositories it generates. Use when planning work, picking up features, or auditing what's missing.
---

# Production Feature Map

This skill provides a structured, actionable backlog of every feature needed to bring `jules-idea-automation` to full production readiness. It covers **two dimensions**:

1. **The Tool** — The CLI itself (`jules-idea-automation`): resilience, testing, observability, distribution, and developer experience.
2. **Generated Repos** — The repositories this tool creates: scaffold quality, language support, CI/CD injection, and handoff polish.

## How to Use This Skill

### For Agents
1. Read `CHECKLIST.md` in this directory to see all features, their priorities, and acceptance criteria.
2. Pick any `[ ]` (uncompleted) item. Mark it `[/]` (in-progress) when starting work.
3. Implement the feature following the **Affected Files** guidance.
4. Mark it `[x]` (complete) when the acceptance criteria are met and tests pass.
5. Do **not** modify items outside your scope — follow the "Hyper-Focused Execution" directive.

### For Developers
- Use `CHECKLIST.md` as a living backlog. Filter by priority (P0–P3) to decide what to work on next.
- Each item includes acceptance criteria so you know exactly when it's done.
- Items are grouped by domain area for easy scanning.

### Priority Levels
| Label | Meaning |
|-------|---------|
| **P0** | Critical — blocks production use or has active user impact |
| **P1** | High — important for reliability, DX, or security |
| **P2** | Medium — meaningful improvement, schedule when capacity allows |
| **P3** | Low — nice-to-have, polish, or future-looking |

### Status Markers
- `[ ]` — Not started
- `[/]` — In progress
- `[x]` — Complete

## Architecture Context

```
jules-idea-automation/
├── main.py                 # Entry point (orchestration only)
├── src/
│   ├── cli/                # Argument parsing, command handlers
│   │   ├── commands.py     # handle_agent, handle_website, handle_manual, etc.
│   │   └── parser.py       # argparse configuration
│   ├── core/               # Workflow engine, domain models, events
│   │   ├── workflow.py     # IdeaWorkflow orchestrator (DI-based)
│   │   ├── models.py       # IdeaResponse, ProjectScaffold, WorkflowResult
│   │   ├── interfaces.py   # EventBus, CacheProvider, EventHandler protocols
│   │   ├── events.py       # WorkflowStarted, WorkflowCompleted domain events
│   │   └── readme_builder.py
│   ├── services/           # External API clients
│   │   ├── gemini.py       # Idea generation + scaffold generation (Gemini 3)
│   │   ├── github.py       # Repo creation + Git Data API batch commits
│   │   ├── jules.py        # Session lifecycle (create, watch, approve, message)
│   │   ├── scraper.py      # Web scraping with SSRF protection
│   │   ├── cache.py        # FileCacheProvider (disk-based API response cache)
│   │   ├── audit.py        # JsonFileAuditLogger (JSONL event log)
│   │   └── bus.py          # LocalEventBus + NullEventBus
│   ├── templates/scaffold/ # 9 fallback scaffold template files
│   ├── templates/feature_map.py  # MVP + Production checklists (AI or static w/ TEMPLATE notice)
│   └── utils/              # Cross-cutting concerns
│       ├── errors.py       # Custom exception hierarchy
│       ├── guide.py        # In-CLI guide system
│       ├── polling.py      # Generic poll_until / poll_with_result
│       ├── reporter.py     # Rich console output (panels, spinners)
│       ├── security.py     # SSRF validation (DNS resolution)
│       └── slugify.py      # Title → kebab-case slug
└── tests/                  # Mirror structure with pytest
```

## Key Workflow
```
User Input → Gemini (idea/scaffold) → GitHub (repo + atomic commit) → Jules (session + watch)
```

## Existing Completed Phases (for reference)
- Phase 1: Core Integration (Gemini → GitHub → Jules)
- Phase 2: Category-aware prompts, enriched output
- Phase 3: Session monitoring, PR detection
- Phase 4: Multi-file scaffold, fallback, retry
- Phase 5: Interactive refinement (sendMessage, approve_plan)
- Phase 6: SOLID refactor (modular layers)
- Phase 7: Manual mode (custom ideas, slugify, tech_stack/features)
- Phase 8 (partial): CLI guide, input validation (in progress)
- Phase 9: Paste-content input modes (`paste`, `website --content`)
- Phase 10: Checklist template clarity & project-aware production items
