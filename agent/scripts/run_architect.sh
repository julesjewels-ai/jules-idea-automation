#!/bin/bash
# Run Architect Agent
# Reads PRD.md and GUARDRAILS.md, produces ARCHITECTURE.md and interface stubs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
CONFIG_FILE="$PROJECT_ROOT/agent/config/architect.config.json"
PROMPT_FILE="$PROJECT_ROOT/agent/prompts/architect_prompt.md"
LOG_FILE="$PROJECT_ROOT/logs/architect.log"

# Load config
MAX_ITERATIONS=$(jq -r '.max_iterations' "$CONFIG_FILE")
TIMEOUT=$(jq -r '.timeout_seconds' "$CONFIG_FILE")
SUCCESS_MARKER=$(jq -r '.success_marker' "$CONFIG_FILE")

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "=== Architect Agent ===" | tee -a "$LOG_FILE"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_FILE"
echo "Max iterations: $MAX_ITERATIONS" | tee -a "$LOG_FILE"
echo "Timeout: ${TIMEOUT}s" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check required inputs
for input in PRD.md GUARDRAILS.md; do
    if [[ ! -f "$PROJECT_ROOT/$input" ]]; then
        echo "ERROR: Required input missing: $input" | tee -a "$LOG_FILE"
        exit 1
    fi
done

iteration=0
success=false

while [[ $iteration -lt $MAX_ITERATIONS ]]; do
    ((iteration++))
    echo "--- Iteration $iteration ---" | tee -a "$LOG_FILE"
    
    # Run agent (placeholder - replace with actual agent invocation)
    # Example: jules run --prompt "$PROMPT_FILE" --context "$PROJECT_ROOT" 2>&1 | tee -a "$LOG_FILE"
    
    # Check for success marker in output or in created files
    if grep -rq "$SUCCESS_MARKER" "$LOG_FILE" 2>/dev/null; then
        echo "SUCCESS: $SUCCESS_MARKER detected" | tee -a "$LOG_FILE"
        success=true
        break
    fi
    
    # Check for failure patterns
    for pattern in $(jq -r '.failure_patterns[]' "$CONFIG_FILE"); do
        if grep -q "$pattern" "$LOG_FILE" 2>/dev/null; then
            echo "FAILURE: $pattern detected" | tee -a "$LOG_FILE"
            exit 1
        fi
    done
    
    # Run verification commands
    all_verified=true
    while IFS= read -r cmd; do
        if ! (cd "$PROJECT_ROOT" && eval "$cmd" >/dev/null 2>&1); then
            all_verified=false
            break
        fi
    done < <(jq -r '.verification_commands[]' "$CONFIG_FILE")
    
    if $all_verified; then
        echo "SUCCESS: All verification commands passed" | tee -a "$LOG_FILE"
        echo "$SUCCESS_MARKER" | tee -a "$LOG_FILE"
        success=true
        break
    fi
    
    sleep 1
done

echo "" | tee -a "$LOG_FILE"
echo "Completed: $(date -Iseconds)" | tee -a "$LOG_FILE"
echo "Iterations: $iteration" | tee -a "$LOG_FILE"

if $success; then
    echo "Status: SUCCESS" | tee -a "$LOG_FILE"
    exit 0
else
    echo "Status: ITERATION_LIMIT" | tee -a "$LOG_FILE"
    exit 1
fi
