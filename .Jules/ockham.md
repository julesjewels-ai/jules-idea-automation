## 2025-05-26 - [Dead Code Removal] **Observation:** Found `tool.py` referencing non-existent modules (`src.jules_client`) and duplicate/transitional top-level service files (`src/gemini_client.py`, etc.) that were superseded by `src/services/`. This created confusion and potential security risks (`src/scraper.py` lacked SSRF protection). **Action:** Deleted `tool.py`, `src/gemini_client.py`, `src/github_client.py`, and `src/scraper.py`. Verified no usages in active codebase via grep and tests.

## 2026-01-28 - [Complexity Reduction]
**Target:** `print_panel` in `src/utils/reporter.py`
**Delta:** Complexity Score 13 -> 3
**Summary:** Extracted border creation and text wrapping logic into `_create_top_border` and `_wrap_content` helper functions. This simplified the main `print_panel` function significantly while maintaining identical output behavior.

## 2026-01-31 - [Complexity Reduction]
**Target:** `watch_session` in `src/cli/commands.py`
**Observation:** `watch_session` contained a manual polling loop mixed with UI update logic, violating Single Responsibility Principle and duplicating polling patterns found in `src.utils.polling`.
**Action:** Refactored `watch_session` to delegate polling to `poll_with_result`. Updated `poll_with_result` to return elapsed time, satisfying the command's requirements. Added comprehensive tests in `tests/cli/test_watch_session.py`.
