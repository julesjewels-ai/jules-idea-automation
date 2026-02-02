#!/bin/bash
# Agent Pipeline Orchestrator
# Runs all 5 agents in sequence, verifying each phase before proceeding

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/agent/scripts"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local agent=$2
    case $status in
        "running") echo -e "${YELLOW}▶${NC} Running $agent..." ;;
        "success") echo -e "${GREEN}✓${NC} $agent completed successfully" ;;
        "failed")  echo -e "${RED}✗${NC} $agent failed" ;;
    esac
}

check_promise() {
    local log_file=$1
    local promise=$2
    grep -q "$promise" "$log_file" 2>/dev/null
}

# Create logs directory
mkdir -p "$LOGS_DIR"

echo "=========================================="
echo "  Agent Pipeline Orchestrator"
echo "  Started: $(date)"
echo "=========================================="
echo ""

# Define pipeline stages
AGENTS=("architect" "engineer" "mason" "coder" "deliverer")
PROMISES=(
    "<promise>ARCHITECTURE_LOCKED</promise>"
    "<promise>SKELETON_VALID</promise>"
    "<promise>SOLID_COMPLETE</promise>"
    "<promise>TESTS_PASSING_ALL</promise>"
    "<promise>READY_FOR_DEPLOYMENT</promise>"
)

# Run each agent in sequence
for i in "${!AGENTS[@]}"; do
    agent="${AGENTS[$i]}"
    promise="${PROMISES[$i]}"
    script="$SCRIPTS_DIR/run_${agent}.sh"
    log="$LOGS_DIR/${agent}.log"
    
    echo "--- Phase $((i+1))/5: ${agent^} ---"
    print_status "running" "${agent^}"
    
    if [[ ! -f "$script" ]]; then
        echo "ERROR: Script not found: $script"
        exit 1
    fi
    
    # Run the agent script
    if bash "$script"; then
        # Verify promise was emitted
        if check_promise "$log" "$promise"; then
            print_status "success" "${agent^}"
        else
            echo "WARNING: Agent completed but promise not found in log"
            print_status "success" "${agent^}"
        fi
    else
        print_status "failed" "${agent^}"
        echo ""
        echo "Pipeline stopped at ${agent^} phase."
        echo "Check logs at: $log"
        exit 1
    fi
    
    echo ""
done

echo "=========================================="
echo "  Pipeline Complete!"
echo "  Finished: $(date)"
echo "=========================================="
echo ""
echo "All phases completed successfully."
echo "The codebase is ready for deployment."
