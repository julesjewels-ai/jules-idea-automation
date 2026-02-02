# Success Criteria

> Machine-checkable signals for each development phase.  
> Agents emit `<promise>PHASE_NAME</promise>` when criteria are met.

---

## Phase: ARCHITECTURE_LOCKED

**Owner:** Architect Agent  
**Promise Token:** `<promise>ARCHITECTURE_LOCKED</promise>`

### Required Files

| File | Description | Validation |
|------|-------------|------------|
| `PRD.md` | Requirements document | Exists, has "APPROVED" status |
| `ARCHITECTURE.md` | System design | Exists, has component diagram |
| `src/core/interfaces.py` | Domain interfaces | Has at least 1 ABC defined |

### Verification Commands

```bash
# All required files exist
test -f PRD.md && test -f ARCHITECTURE.md && test -f src/core/interfaces.py

# Interfaces file has content
grep -q "class.*ABC" src/core/interfaces.py
```

---

## Phase: SKELETON_VALID

**Owner:** Engineer Agent  
**Promise Token:** `<promise>SKELETON_VALID</promise>`

### Required Structure

```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── interfaces.py    # ABCs defined
│   ├── models.py        # Data models
│   └── domain.py        # Domain logic stubs
├── services/
│   └── __init__.py
├── adapters/
│   └── __init__.py
└── cli/ or app.py       # Entrypoint
```

### Verification Commands

```bash
# Python syntax valid across all source files
python -m py_compile src/**/*.py

# Imports resolve
python -c "import src; import src.core; import src.services"
```

---

## Phase: SOLID_COMPLETE

**Owner:** Mason Agent  
**Promise Token:** `<promise>SOLID_COMPLETE</promise>`

### Requirements

| Criterion | Target | Verification |
|-----------|--------|--------------|
| Interface coverage | All services have ABCs | `grep -r "ABC" src/core/interfaces.py` |
| Dependency injection | No hardcoded deps in services | Manual review |
| Test coverage | ≥60% on `src/core/` | `pytest --cov=src/core --cov-fail-under=60` |

### Verification Commands

```bash
# Tests exist and pass
pytest tests/ -v

# Coverage threshold met
pytest --cov=src/core --cov-report=term-missing --cov-fail-under=60
```

---

## Phase: TESTS_PASSING_ALL

**Owner:** Coder Agent  
**Promise Token:** `<promise>TESTS_PASSING_ALL</promise>`

### Requirements

| Criterion | Target | Verification |
|-----------|--------|--------------|
| All tests pass | 100% green | `pytest tests/ --tb=short` |
| Coverage overall | ≥80% | `pytest --cov=src --cov-fail-under=80` |
| No skipped tests | 0 skipped | `pytest --strict-markers` |

### Verification Commands

```bash
# Full test suite passes
pytest tests/ -v --tb=short

# Coverage meets threshold
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# No warnings treated as errors (optional)
pytest tests/ -W error::DeprecationWarning
```

---

## Phase: READY_FOR_DEPLOYMENT

**Owner:** Deliverer Agent  
**Promise Token:** `<promise>READY_FOR_DEPLOYMENT</promise>`

### Requirements

| Criterion | Command | Expected |
|-----------|---------|----------|
| Linting passes | `make lint` | Exit code 0 |
| Type checking passes | `make typecheck` | Exit code 0 (or skip if not configured) |
| Security scan clean | `bandit -r src/ -ll` | No high/critical findings |
| Build succeeds | `make build` | Exit code 0 |
| Documentation current | `test -f README.md` | README exists with usage section |

### Verification Commands

```bash
# Lint check
make lint

# Type check (if configured)
make typecheck || echo "Typecheck not configured, skipping"

# Security scan
bandit -r src/ -ll -x tests/

# Build (package or Docker)
make build

# Documentation exists
grep -q "## Usage" README.md
```

---

## Quick Reference

| Phase | Token | Key Command |
|-------|-------|-------------|
| ARCHITECTURE_LOCKED | `<promise>ARCHITECTURE_LOCKED</promise>` | File existence checks |
| SKELETON_VALID | `<promise>SKELETON_VALID</promise>` | `python -m py_compile src/**/*.py` |
| SOLID_COMPLETE | `<promise>SOLID_COMPLETE</promise>` | `pytest --cov-fail-under=60` |
| TESTS_PASSING_ALL | `<promise>TESTS_PASSING_ALL</promise>` | `pytest --cov-fail-under=80` |
| READY_FOR_DEPLOYMENT | `<promise>READY_FOR_DEPLOYMENT</promise>` | `make lint && make build` |

---

## Failure Tokens

Agents emit these on failure conditions:

| Token | Meaning | Recovery |
|-------|---------|----------|
| `CONTEXT_POLLUTED` | Too many failed attempts | Reset context, summarize blockers |
| `ITERATION_LIMIT` | Max iterations reached | Document progress, escalate |
| `DEPENDENCY_MISSING` | Required dependency unavailable | Install or document blocker |
| `HUMAN_REVIEW_REQUIRED` | Decision beyond agent authority | Create issue, await human |
