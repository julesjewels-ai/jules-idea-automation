# Agent Guardrails

> Hard constraints for automated agents operating on this repository.  
> **Agents MUST NOT violate these rules under any circumstances.**

---

## Technology Stack

### Allowed

| Category | Technologies |
|----------|--------------|
| Language | Python 3.9+ |
| Framework | Click (CLI), FastAPI (API) |
| Testing | pytest, pytest-cov |
| Linting | ruff, black, mypy |
| Dependencies | See `requirements.txt` |

### Forbidden

| Technology | Reason |
|------------|--------|
| ORMs (SQLAlchemy, Django ORM) | Keep data access explicit for now |
| Heavy frameworks (Django) | Overkill for current scope |
| Async unless necessary | Adds complexity without benefit |

---

## Security & Privacy

### Data Handling

- **NO hardcoded secrets** - All credentials via environment variables
- **NO logging of PII** - Mask or exclude sensitive fields
- **NO committing `.env`** - Must be in `.gitignore`

### API Keys

| Key | Source | Scope |
|-----|--------|-------|
| `GEMINI_API_KEY` | Google AI Studio | Content generation |
| `GITHUB_TOKEN` | GitHub Settings | Repo creation (repo scope) |
| `JULES_API_KEY` | Jules Platform | Session management |

### Input Validation

- All external input MUST be validated before processing
- Use Pydantic models for structured input
- Implement length limits on text inputs (max 100KB default)

---

## Performance & Cost Limits

### Per Agent Run

| Metric | Limit | Action on Exceed |
|--------|-------|------------------|
| Max iterations | 50 | Terminate with `ITERATION_LIMIT` |
| Max API calls | 100 | Terminate with `API_LIMIT` |
| Max runtime | 30 min | Terminate with `TIMEOUT` |
| Max file changes per commit | 20 | Split into multiple commits |

### Cost Controls

- Prefer smaller models for simple tasks (e.g., `gemini-2.0-flash`)
- Batch API calls where possible
- Cache responses when idempotent

---

## Code Quality

### Mandatory Checks

All code changes MUST pass:

```bash
make lint      # ruff + flake8
make typecheck # mypy (if configured)
make test      # pytest
```

### Style Rules

- Follow PEP 8 (enforced by ruff)
- Max line length: 100 characters
- Docstrings required for public functions
- Type hints required for function signatures

---

## Git Hygiene

### Commit Messages

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example: `feat(cli): add --watch flag for session monitoring`

### Branch Strategy

- `main` - Protected, requires PR
- `feature/*` - Feature development
- `fix/*` - Bug fixes
- `agent/*` - Agent-generated changes (auto-merged if tests pass)

---

## Context Management

### Rotation Policy

Agents SHOULD rotate context when:

- Same command fails 3+ consecutive times
- Diff size churn exceeds 500 lines in one iteration
- Token count approaches model limit (reserve 20% for response)

### State Persistence

- Long-lived state MUST be persisted to files, not prompt memory
- Use git commits as checkpoints
- Progress markers in designated files (see `SUCCESS_CRITERIA.md`)

---

## Escalation Paths

### When to Stop and Escalate

| Condition | Action |
|-----------|--------|
| Security vulnerability detected | STOP, create issue, notify human |
| Breaking change to public API | STOP, request human review |
| Unclear requirements | STOP, document question in PRD.md |
| 3+ failed iterations on same task | STOP, emit `CONTEXT_POLLUTED` |

### Recovery Actions

```
CONTEXT_POLLUTED → Reset to last known good commit, summarize blockers
ITERATION_LIMIT  → Document progress, list remaining tasks
API_LIMIT        → Checkpoint work, schedule continuation
```
