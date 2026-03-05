1. **Understand CI Failure:** The CI job `Lint & Test (Python 3.12)` failed on `ruff format --check src/ tests/` with the error `Would reformat: src/services/github.py`.
2. **Action Plan:**
   - Since `ruff format` failed on `src/services/github.py`, I will run `ruff format src/services/github.py` locally to automatically fix the formatting issue.
   - Run `ruff format --check src/ tests/` locally to verify that all files are formatted correctly.
   - Complete pre-commit instructions.
   - Submit the fix.
