# Context Health Policy

> Guidelines for managing context pollution and maintaining agent productivity.

---

## Context Rotation Triggers

Agents SHOULD request context rotation when:

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Repeated command failure | Same command fails 3+ times | Reset to last commit, summarize blocker |
| Diff churn | >500 lines changed in single iteration | Checkpoint and reassess approach |
| Token exhaustion | >80% of context window used | Summarize progress, start fresh context |
| Circular reasoning | Same fix attempted 2+ times | Document in progress file, try different approach |

---

## State Persistence Rules

### ✅ DO persist in files/git:

- Progress summaries → `*_PROGRESS.txt` or `*_REPORT.md`
- Architectural decisions → `ARCHITECTURE.md`
- Blockers and questions → Create GitHub Issue
- Iteration counts and timestamps → Log files
- Intermediate results → Commit to `agent/*` branch

### ❌ DO NOT rely on:

- Transient prompt memory for long-lived state
- Uncommitted file changes across context rotations
- Assumptions about previous conversation context

---

## Progress File Standards

Each agent maintains a progress file with this format:

```markdown
# [Agent] Progress

## Session Info
- Started: YYYY-MM-DD HH:MM:SS
- Iteration: N
- Status: IN_PROGRESS | COMPLETE | BLOCKED

## Completed
- [x] Task 1
- [x] Task 2

## In Progress
- [ ] Current task

## Blockers
- Blocker description (if any)

## Next Steps
- Step 1
- Step 2
```

---

## Recovery Procedures

### On CONTEXT_POLLUTED:

1. Commit any valuable changes with message: `wip: context rotation checkpoint`
2. Create progress summary in appropriate `*_PROGRESS.txt`
3. Reset working tree to last known good state
4. Start new context with summary from progress file

### On ITERATION_LIMIT:

1. Document what was attempted in progress file
2. List remaining tasks explicitly
3. Create GitHub Issue if human intervention needed
4. Exit with clear status for orchestrator

### On API_LIMIT:

1. Checkpoint all work immediately
2. Update progress file with current state
3. Schedule continuation run
4. Exit gracefully

---

## Git Hygiene for Agents

### Branch Strategy

```
main              ← Protected, human merge only
├── agent/architect  ← Architect work
├── agent/engineer   ← Engineer work
├── agent/mason      ← Mason work
├── agent/coder      ← Coder work
└── agent/deliverer  ← Deliverer work
```

### Commit Frequency

- Commit after each successful subtask
- Commit before any potentially destructive operation
- Commit with meaningful messages following conventional commits

### Commit Message Format

```
<type>(<agent>): <description>

[optional body]

[optional footer with iteration count]
Iteration: N/MAX
```

Types: `arch`, `eng`, `mason`, `code`, `deliver`, `fix`, `test`, `docs`

---

## Monitoring & Observability

### Log Files (git-ignored)

```
logs/
├── architect.log   ← Timestamped iteration logs
├── engineer.log
├── mason.log
├── coder.log
├── deliverer.log
└── pipeline.log    ← Orchestrator summary
```

### Progress Markers (git-tracked)

```
ARCHITECTURE.md         ← Architect output (versioned)
ENGINEER_PROGRESS.txt   ← Engineer status
MASON_REPORT.md         ← Mason summary
CODER_PROGRESS.txt      ← Coder status
DELIVERER_REPORT.md     ← Final verification
```

---

## Emergency Procedures

### If agent appears stuck:

1. Check iteration count in progress file
2. Review last 10 lines of log file
3. If CONTEXT_POLLUTED not emitted automatically:
   - Manually terminate agent script
   - Document state in progress file
   - Reset and retry with simplified scope

### If security issue detected:

1. STOP all agent operations immediately
2. Do NOT commit any changes
3. Create security issue with `security` label
4. Await human review before proceeding
