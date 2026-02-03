"""
Agent-Ready Template Content

Embedded template files for agent-ready repository scaffolding.
These are injected into new repositories during CLI creation.
"""

from typing import Dict, List

# =============================================================================
# PROJECT CONTRACTS
# =============================================================================

PRD_TEMPLATE = """# Product Requirements Document (PRD)

> **Status:** `DRAFT` | `IN_REVIEW` | `APPROVED`  
> **Last Updated:** YYYY-MM-DD  
> **Owner:** [Agent/Human Name]

---

## Problem Statement

<!-- What problem does this project solve? Who experiences this problem? -->

[Describe the core problem in 2-3 sentences. Be specific about the pain point.]

---

## User Stories

<!-- Format: As a [persona], I want [goal] so that [benefit] -->

| ID | Persona | Goal | Benefit | Priority |
|----|---------|------|---------|----------|
| US-001 | | | | P0/P1/P2 |
| US-002 | | | | |

---

## Acceptance Criteria

### MVP Scope

- [ ] **AC-001:** [Criterion that can be verified]
- [ ] **AC-002:** [Criterion that can be verified]

### V1 Scope

- [ ] **AC-101:** [Criterion that can be verified]

---

## Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Response time | < X ms |
| Reliability | Uptime SLA | 99.X% |

---

## Definition of Done

### MVP Complete When:

- [ ] All MVP acceptance criteria pass
- [ ] Smoke tests run without errors
- [ ] Basic documentation exists

### V1 Complete When:

- [ ] All V1 acceptance criteria pass
- [ ] 80%+ test coverage
- [ ] Security scan passes
"""

GUARDRAILS_TEMPLATE = """# Agent Guardrails

> Hard constraints for automated agents operating on this repository.

---

## Technology Stack

### Allowed

| Category | Technologies |
|----------|--------------|
| Language | Python 3.9+ |
| Testing | pytest, pytest-cov |
| Linting | ruff, black, mypy |

### Forbidden

| Technology | Reason |
|------------|--------|
| Heavy frameworks | Overkill for current scope |

---

## Security & Privacy

- **NO hardcoded secrets** - All credentials via environment variables
- **NO logging of PII** - Mask or exclude sensitive fields
- **NO committing `.env`** - Must be in `.gitignore`

---

## Performance & Cost Limits

| Metric | Limit | Action on Exceed |
|--------|-------|------------------|
| Max iterations | 50 | Terminate with `ITERATION_LIMIT` |
| Max API calls | 100 | Terminate with `API_LIMIT` |
| Max runtime | 30 min | Terminate with `TIMEOUT` |

---

## Context Management

### Rotation Policy

Agents SHOULD rotate context when:
- Same command fails 3+ times
- Diff size churn exceeds 500 lines
- Token count approaches model limit

### State Persistence

- Long-lived state MUST be persisted to files, not prompt memory
- Use git commits as checkpoints

---

## Escalation Paths

| Condition | Action |
|-----------|--------|
| Security vulnerability | STOP, create issue, notify human |
| Breaking change | STOP, request human review |
| 3+ failed iterations | STOP, emit `CONTEXT_POLLUTED` |
"""

SUCCESS_CRITERIA_TEMPLATE = """# Success Criteria

> Machine-checkable signals for each development phase.  
> Agents emit `<promise>PHASE_NAME</promise>` when criteria are met.

---

## Phase: ARCHITECTURE_LOCKED

**Promise Token:** `<promise>ARCHITECTURE_LOCKED</promise>`

### Verification Commands

```bash
test -f ARCHITECTURE.md
test -f src/core/interfaces.py
```

---

## Phase: SKELETON_VALID

**Promise Token:** `<promise>SKELETON_VALID</promise>`

### Verification Commands

```bash
python -m py_compile src/**/*.py
python -c "import src"
```

---

## Phase: SOLID_COMPLETE

**Promise Token:** `<promise>SOLID_COMPLETE</promise>`

### Verification Commands

```bash
pytest tests/ -v
pytest --cov=src/core --cov-fail-under=60
```

---

## Phase: TESTS_PASSING_ALL

**Promise Token:** `<promise>TESTS_PASSING_ALL</promise>`

### Verification Commands

```bash
pytest tests/ -v
pytest --cov=src --cov-fail-under=80
```

---

## Phase: READY_FOR_DEPLOYMENT

**Promise Token:** `<promise>READY_FOR_DEPLOYMENT</promise>`

### Verification Commands

```bash
make lint
make test
bandit -r src/ -ll -x tests/
```

---

## Failure Tokens

| Token | Meaning |
|-------|---------|
| `CONTEXT_POLLUTED` | Too many failed attempts |
| `ITERATION_LIMIT` | Max iterations reached |
| `HUMAN_REVIEW_REQUIRED` | Decision beyond agent authority |
"""

CONTEXT_HEALTH_TEMPLATE = """# Context Health Policy

> Guidelines for managing context pollution and agent productivity.

---

## Context Rotation Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Repeated failure | 3+ times | Reset to last commit |
| Diff churn | >500 lines | Checkpoint and reassess |
| Token exhaustion | >80% used | Summarize and restart |

---

## State Persistence Rules

### ✅ DO persist in files/git:
- Progress summaries → `*_PROGRESS.txt`
- Architectural decisions → `ARCHITECTURE.md`
- Blockers → GitHub Issues

### ❌ DO NOT rely on:
- Transient prompt memory
- Uncommitted file changes

---

## Progress File Format

```markdown
# [Agent] Progress

## Session Info
- Started: YYYY-MM-DD HH:MM:SS
- Iteration: N
- Status: IN_PROGRESS | COMPLETE | BLOCKED

## Completed
- [x] Task 1

## Blockers
- Blocker description
```

---

## Recovery Procedures

### On CONTEXT_POLLUTED:
1. Commit valuable changes
2. Create progress summary
3. Reset to last good state
4. Start new context

### On ITERATION_LIMIT:
1. Document attempts in progress file
2. List remaining tasks
3. Create GitHub Issue if needed
"""

ARCHITECTURE_TEMPLATE = """# Architecture Document

> **Status:** `DRAFT` | `REVIEW` | `LOCKED`  
> **Last Updated:** YYYY-MM-DD

---

## System Overview

[Describe what the system does and its primary purpose]

---

## Component Diagram

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI Interface]
    end
    
    subgraph "Core Domain"
        WF[Workflow Engine]
        Models[Domain Models]
    end
    
    subgraph "Services"
        SVC[Services]
    end
    
    CLI --> WF
    WF --> Models
    WF --> SVC
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.9+ | Team expertise |
| Testing | pytest | Standard, good plugins |
"""

# =============================================================================
# PROGRESS MARKERS
# =============================================================================

ENGINEER_PROGRESS_TEMPLATE = """# Engineer Progress

## Session Info
- Started: YYYY-MM-DD HH:MM:SS
- Iteration: 0
- Status: NOT_STARTED

## Import Verification
- [ ] `python -c "import src"` passes
- [ ] All modules have `__init__.py`

## Blockers

## Next Steps
"""

MASON_REPORT_TEMPLATE = """# Mason Report

## Session Info
- Started: YYYY-MM-DD HH:MM:SS
- Completed: YYYY-MM-DD HH:MM:SS

## Patterns Implemented

## Coverage Summary

| Module | Coverage | Target | Status |
|--------|----------|--------|--------|
| `src/core/` | X% | 60% | ✓/✗ |

## Technical Debt

| ID | Description | Priority |
|----|-------------|----------|
"""

CODER_PROGRESS_TEMPLATE = """# Coder Progress

## Session Info
- Started: YYYY-MM-DD HH:MM:SS
- Iteration: 0
- Status: NOT_STARTED

## Features Implemented

| Feature ID | Description | Tests | Status |
|------------|-------------|-------|--------|

## Test Results Summary

```
Tests: X passed, Y failed
Coverage: Z%
```

## Blockers

## Next Steps
"""

DELIVERER_REPORT_TEMPLATE = """# Deliverer Report

## Session Info
- Started: YYYY-MM-DD HH:MM:SS
- Completed: YYYY-MM-DD HH:MM:SS

## Quality Gate Results

| Check | Command | Status |
|-------|---------|--------|
| Lint | `make lint` | ✓/✗ |
| Tests | `make test` | ✓/✗ |
| Security | `bandit` | ✓/✗ |

## Security Scan Results
- High: 0
- Medium: 0
- Low: 0

## Final Status
**READY_FOR_DEPLOYMENT:** YES / NO
"""

# =============================================================================
# MAKEFILE
# =============================================================================

MAKEFILE_TEMPLATE = """.PHONY: help install lint format test coverage build clean

help:
\t@echo "Available targets:"
\t@echo "  make install  - Install dependencies"
\t@echo "  make lint     - Run linting"
\t@echo "  make format   - Format code"
\t@echo "  make test     - Run tests"
\t@echo "  make coverage - Run tests with coverage"
\t@echo "  make build    - Build package"

install:
\tpip install -r requirements.txt
\tpip install ruff black isort pytest pytest-cov

lint:
\t@echo "Running ruff..."
\truff check src/ tests/ --fix || ruff check src/ tests/

format:
\tblack src/ tests/
\tisort src/ tests/

test:
\tpytest tests/ -v --tb=short

coverage:
\tpytest tests/ -v --cov=src --cov-report=term-missing

coverage-check:
\tpytest tests/ --cov=src --cov-fail-under=80

build:
\t@if [ -f "pyproject.toml" ]; then python -m build; else python -c "import src"; fi

clean:
\trm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
"""

# =============================================================================
# AGENT PROMPTS
# =============================================================================

ARCHITECT_PROMPT = """# Architect Agent Prompt

## Role
You are the **Architect Agent**, responsible for designing the high-level system architecture.

## Mission
Analyze the PRD and produce a complete architectural design.

## Allowed Commands
```bash
cat PRD.md
cat GUARDRAILS.md
echo "..." > ARCHITECTURE.md
mkdir -p src/core
git add . && git commit -m "arch: <description>"
```

## Success Criteria
Emit `<promise>ARCHITECTURE_LOCKED</promise>` when:
- [ ] `ARCHITECTURE.md` exists with component diagram
- [ ] `src/core/interfaces.py` has at least 1 ABC defined

## Failure Conditions
Emit `CONTEXT_POLLUTED` if:
- PRD.md is missing or has "DRAFT" status
- Requirements are ambiguous after 3 attempts
"""

ENGINEER_PROMPT = """# Engineer Agent Prompt

## Role
You are the **Engineer Agent**, responsible for generating the code skeleton.

## Mission
Transform the architectural design into a valid, importable code skeleton.

## Allowed Commands
```bash
cat ARCHITECTURE.md
mkdir -p src/{core,services,adapters}
python -m py_compile src/**/*.py
git add . && git commit -m "eng: <description>"
```

## Success Criteria
Emit `<promise>SKELETON_VALID</promise>` when:
- [ ] All modules from ARCHITECTURE.md exist
- [ ] `python -c "import src"` succeeds

## Failure Conditions
Emit `CONTEXT_POLLUTED` if:
- ARCHITECTURE.md is missing
- Circular import detected after 3 attempts
"""

MASON_PROMPT = """# Mason Agent Prompt

## Role
You are the **Mason Agent**, responsible for implementing SOLID patterns.

## Mission
Solidify the codebase with proper software engineering patterns.

## Allowed Commands
```bash
cat src/core/interfaces.py
pytest tests/ -v --cov=src/core
git add . && git commit -m "mason: <description>"
```

## Success Criteria
Emit `<promise>SOLID_COMPLETE</promise>` when:
- [ ] All services use dependency injection
- [ ] `pytest --cov=src/core --cov-fail-under=60` passes

## Failure Conditions
Emit `CONTEXT_POLLUTED` if:
- Skeleton is invalid (syntax errors)
- Cannot achieve 60% coverage after 5 attempts
"""

CODER_PROMPT = """# Coder Agent Prompt

## Role
You are the **Coder Agent**, responsible for implementing business logic.

## Mission
Complete the implementation of all features defined in the PRD.

## Allowed Commands
```bash
cat PRD.md
pytest tests/ -v --cov=src --cov-fail-under=80
git add . && git commit -m "feat: <description>"
```

## Success Criteria
Emit `<promise>TESTS_PASSING_ALL</promise>` when:
- [ ] All acceptance criteria from PRD.md have tests
- [ ] `pytest --cov=src --cov-fail-under=80` passes

## Failure Conditions
Emit `CONTEXT_POLLUTED` if:
- Tests consistently fail after 5 fix attempts
"""

DELIVERER_PROMPT = """# Deliverer Agent Prompt

## Role
You are the **Deliverer Agent**, responsible for final verification.

## Mission
Ensure the codebase is production-ready.

## Allowed Commands
```bash
make lint
make test
bandit -r src/ -ll -x tests/
git add . && git commit -m "chore: prepare for deployment"
```

## Success Criteria
Emit `<promise>READY_FOR_DEPLOYMENT</promise>` when:
- [ ] `make lint` exits 0
- [ ] `make test` exits 0
- [ ] `bandit` shows no high/critical issues

## Failure Conditions
Emit `HUMAN_REVIEW_REQUIRED` if:
- Security vulnerabilities detected
"""

# =============================================================================
# AGENT CONFIGS
# =============================================================================

ARCHITECT_CONFIG = """{
  "agent": "architect",
  "max_iterations": 50,
  "timeout_seconds": 1800,
  "success_marker": "<promise>ARCHITECTURE_LOCKED</promise>",
  "failure_patterns": ["CONTEXT_POLLUTED", "HUMAN_REVIEW_REQUIRED"],
  "prompt_file": "agent/prompts/architect_prompt.md",
  "verification_commands": [
    "test -f ARCHITECTURE.md",
    "test -f src/core/interfaces.py"
  ]
}"""

ENGINEER_CONFIG = """{
  "agent": "engineer",
  "max_iterations": 50,
  "timeout_seconds": 1800,
  "success_marker": "<promise>SKELETON_VALID</promise>",
  "failure_patterns": ["CONTEXT_POLLUTED"],
  "prompt_file": "agent/prompts/engineer_prompt.md",
  "verification_commands": [
    "python -m py_compile src/core/*.py",
    "python -c 'import src'"
  ]
}"""

MASON_CONFIG = """{
  "agent": "mason",
  "max_iterations": 50,
  "timeout_seconds": 1800,
  "success_marker": "<promise>SOLID_COMPLETE</promise>",
  "failure_patterns": ["CONTEXT_POLLUTED"],
  "prompt_file": "agent/prompts/mason_prompt.md",
  "verification_commands": [
    "pytest tests/ -v",
    "pytest --cov=src/core --cov-fail-under=60"
  ]
}"""

CODER_CONFIG = """{
  "agent": "coder",
  "max_iterations": 100,
  "timeout_seconds": 3600,
  "success_marker": "<promise>TESTS_PASSING_ALL</promise>",
  "failure_patterns": ["CONTEXT_POLLUTED"],
  "prompt_file": "agent/prompts/coder_prompt.md",
  "verification_commands": [
    "pytest tests/ -v",
    "pytest --cov=src --cov-fail-under=80"
  ]
}"""

DELIVERER_CONFIG = """{
  "agent": "deliverer",
  "max_iterations": 30,
  "timeout_seconds": 1200,
  "success_marker": "<promise>READY_FOR_DEPLOYMENT</promise>",
  "failure_patterns": ["CONTEXT_POLLUTED", "HUMAN_REVIEW_REQUIRED"],
  "prompt_file": "agent/prompts/deliverer_prompt.md",
  "verification_commands": [
    "make lint",
    "make test"
  ]
}"""

# =============================================================================
# RUN SCRIPTS
# =============================================================================

RUN_ARCHITECT_SCRIPT = """#!/bin/bash
# Run Architect Agent
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
CONFIG_FILE="$PROJECT_ROOT/agent/config/architect.config.json"
LOG_FILE="$PROJECT_ROOT/logs/architect.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Architect Agent ===" | tee -a "$LOG_FILE"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_FILE"

# Placeholder for agent invocation
# Add your agent runner command here

echo "Completed: $(date -Iseconds)" | tee -a "$LOG_FILE"
"""

RUN_ENGINEER_SCRIPT = """#!/bin/bash
# Run Engineer Agent
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="$PROJECT_ROOT/logs/engineer.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Engineer Agent ===" | tee -a "$LOG_FILE"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_FILE"

# Placeholder for agent invocation
echo "Completed: $(date -Iseconds)" | tee -a "$LOG_FILE"
"""

RUN_MASON_SCRIPT = """#!/bin/bash
# Run Mason Agent
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="$PROJECT_ROOT/logs/mason.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Mason Agent ===" | tee -a "$LOG_FILE"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_FILE"

# Placeholder for agent invocation
echo "Completed: $(date -Iseconds)" | tee -a "$LOG_FILE"
"""

RUN_CODER_SCRIPT = """#!/bin/bash
# Run Coder Agent
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="$PROJECT_ROOT/logs/coder.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Coder Agent ===" | tee -a "$LOG_FILE"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_FILE"

# Placeholder for agent invocation
echo "Completed: $(date -Iseconds)" | tee -a "$LOG_FILE"
"""

RUN_DELIVERER_SCRIPT = """#!/bin/bash
# Run Deliverer Agent
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="$PROJECT_ROOT/logs/deliverer.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Deliverer Agent ===" | tee -a "$LOG_FILE"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_FILE"

# Placeholder for agent invocation
echo "Completed: $(date -Iseconds)" | tee -a "$LOG_FILE"
"""

RUN_PIPELINE_SCRIPT = """#!/bin/bash
# Agent Pipeline Orchestrator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/agent/scripts"

echo "=========================================="
echo "  Agent Pipeline Orchestrator"
echo "  Started: $(date)"
echo "=========================================="

AGENTS=("architect" "engineer" "mason" "coder" "deliverer")

for agent in "${AGENTS[@]}"; do
    echo "--- Running ${agent^} ---"
    bash "$SCRIPTS_DIR/run_${agent}.sh" || {
        echo "Pipeline stopped at ${agent}"
        exit 1
    }
done

echo "=========================================="
echo "  Pipeline Complete!"
echo "=========================================="
"""

# =============================================================================
# PYTEST CONFIG
# =============================================================================

PYTEST_INI = """[pytest]
pythonpath = .
testpaths = tests
addopts = -v --tb=short
"""

# =============================================================================
# SMOKE TEST
# =============================================================================

SMOKE_TEST = '''"""Smoke tests to verify test infrastructure."""

import pytest

class TestSmoke:
    def test_harness_runs(self):
        """Verify pytest can run."""
        assert True
    
    def test_python_version(self):
        """Verify Python version."""
        import sys
        assert sys.version_info >= (3, 9)
'''

# =============================================================================
# GITIGNORE ADDITIONS
# =============================================================================

GITIGNORE_ADDITIONS = """
# Agent Run Artifacts
logs/
.cache/
*.tmp
*.bak

# Coverage
htmlcov/
.coverage
coverage.xml

# Build
dist/
build/
*.egg-info/

# Type checking
.mypy_cache/
.ruff_cache/
"""

# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

AGENT_TEMPLATES: Dict[str, str] = {
    # Project Contracts → docs/
    "docs/PRD.md": PRD_TEMPLATE,
    "docs/GUARDRAILS.md": GUARDRAILS_TEMPLATE,
    "docs/SUCCESS_CRITERIA.md": SUCCESS_CRITERIA_TEMPLATE,
    "docs/CONTEXT_HEALTH.md": CONTEXT_HEALTH_TEMPLATE,
    "docs/ARCHITECTURE.md": ARCHITECTURE_TEMPLATE,
    # Progress Markers → progress/
    "progress/ENGINEER_PROGRESS.txt": ENGINEER_PROGRESS_TEMPLATE,
    "progress/MASON_REPORT.md": MASON_REPORT_TEMPLATE,
    "progress/CODER_PROGRESS.txt": CODER_PROGRESS_TEMPLATE,
    "progress/DELIVERER_REPORT.md": DELIVERER_REPORT_TEMPLATE,
    # Build Configuration (root level - standard locations)
    "Makefile": MAKEFILE_TEMPLATE,
    "pytest.ini": PYTEST_INI,
    # Agent Prompts
    "agent/prompts/architect_prompt.md": ARCHITECT_PROMPT,
    "agent/prompts/engineer_prompt.md": ENGINEER_PROMPT,
    "agent/prompts/mason_prompt.md": MASON_PROMPT,
    "agent/prompts/coder_prompt.md": CODER_PROMPT,
    "agent/prompts/deliverer_prompt.md": DELIVERER_PROMPT,
    # Agent Configs
    "agent/config/architect.config.json": ARCHITECT_CONFIG,
    "agent/config/engineer.config.json": ENGINEER_CONFIG,
    "agent/config/mason.config.json": MASON_CONFIG,
    "agent/config/coder.config.json": CODER_CONFIG,
    "agent/config/deliverer.config.json": DELIVERER_CONFIG,
    # Run Scripts
    "agent/scripts/run_architect.sh": RUN_ARCHITECT_SCRIPT,
    "agent/scripts/run_engineer.sh": RUN_ENGINEER_SCRIPT,
    "agent/scripts/run_mason.sh": RUN_MASON_SCRIPT,
    "agent/scripts/run_coder.sh": RUN_CODER_SCRIPT,
    "agent/scripts/run_deliverer.sh": RUN_DELIVERER_SCRIPT,
    # Pipeline Orchestrator (root level)
    "run_pipeline.sh": RUN_PIPELINE_SCRIPT,
    # Smoke Test
    "tests/test_smoke.py": SMOKE_TEST,
}


def get_agent_template_files() -> List[Dict[str, str]]:
    """
    Returns list of agent template files for GitHub API.

    Returns:
        List of dicts with 'path' and 'content' keys.
    """
    return [{"path": path, "content": content} for path, content in AGENT_TEMPLATES.items()]


def get_gitignore_additions() -> str:
    """Returns additional .gitignore entries for agent runs."""
    return GITIGNORE_ADDITIONS
