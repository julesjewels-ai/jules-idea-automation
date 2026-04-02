# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the tool
python main.py <command>

# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/core/test_workflow.py -v

# Run a single test by name
python -m pytest tests/core/test_workflow.py::test_name -v

# Lint
ruff check src/ tests/

# Format
black --line-length 120 .
isort --profile black --line-length 120 .

# Type check
mypy src/
```

## Environment

Copy `.env.example` to `.env` and populate:
- `GEMINI_API_KEY` — required for all execution commands (and the only key needed in `--demo` mode)
- `GITHUB_TOKEN` — required for repo creation
- `JULES_API_KEY` — required for Jules session management

## Architecture

The tool automates: **idea → GitHub repo → Jules session**.

### Entry point & CLI
- `main.py` — thin orchestrator: parses args, dispatches command, handles top-level error display
- `src/cli/parser.py` — all argparse definitions; commands: `agent`, `website`, `paste`, `manual`, `status`, `list-sources`, `list`, `guide`
- `src/cli/commands.py` — re-exports handlers and the `dispatch_command` function
- Each command lives in its own `src/cli/cmd_*.py` module

### Core workflow
`IdeaWorkflow` (`src/core/workflow.py`) is the main orchestrator:
1. Creates GitHub repo (`GitHubClient`)
2. Calls Gemini to generate a scaffold → commits files to repo
3. Polls Jules until it indexes the repo, then creates a Jules session

Steps 2 and 3 are recoverable failures — the workflow continues and reports partial success.

### Services (dependency-injectable)
- `src/services/gemini.py` — `GeminiClient`: generates ideas, scaffolds, and feature maps using `gemini-2.5-flash`; responses cached via `FileCacheProvider` (`.cache/gemini/`)
- `src/services/github.py` — `GitHubClient`: repo creation, file commits (single and batch)
- `src/services/jules.py` — `JulesClient`: lists sources, creates sessions, checks status
- `src/services/scraper.py` — web scraping for the `website` command
- `src/services/bus.py` — `InMemoryEventBus` / `NullEventBus`
- `src/services/audit.py` — `JsonFileAuditLogger`: writes domain events to `.jules_history.jsonl`
- `src/services/db.py` — `HistoryDB`: SQLite at `~/.jules/history.db`; always use as context manager

### Core models & interfaces
- `src/core/models.py` — Pydantic models: `IdeaResponse`, `ProjectScaffold`, `FeatureMapResponse`, `WorkflowResult`
- `src/core/interfaces.py` — `EventBus`, `EventHandler`, `CacheProvider` protocols
- `src/core/events.py` — domain events (`WorkflowStarted`, `WorkflowCompleted`, etc.)
- `src/templates/feature_map.py` — renders MVP and production feature-map markdown files committed to generated repos

### Utilities
- `src/utils/config.py` — `validate_env_keys()` runs before every command; `preflight_check_credentials()` for token validation
- `src/utils/errors.py` — `AppError` hierarchy (`ConfigurationError`, `GenerationError`, `AuditError`, etc.)
- `src/utils/reporter.py` — Rich-style terminal output: `Spinner`, `print_panel`, `print_workflow_report`
- `src/utils/polling.py` — `poll_until()` used to wait for Jules to index a new repo

### DI pattern
`IdeaWorkflow.__init__` accepts optional `github`, `gemini`, `jules`, `event_bus` — pass mocks in tests rather than patching.
