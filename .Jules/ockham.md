## 2025-05-26 - [Dead Code Removal] **Observation:** Found `tool.py` referencing non-existent modules (`src.jules_client`) and duplicate/transitional top-level service files (`src/gemini_client.py`, etc.) that were superseded by `src/services/`. This created confusion and potential security risks (`src/scraper.py` lacked SSRF protection). **Action:** Deleted `tool.py`, `src/gemini_client.py`, `src/github_client.py`, and `src/scraper.py`. Verified no usages in active codebase via grep and tests.

## 2026-01-28 - [Complexity Reduction]
**Target:** `print_panel` in `src/utils/reporter.py`
**Delta:** Complexity Score 13 -> 3
**Summary:** Extracted border creation and text wrapping logic into `_create_top_border` and `_wrap_content` helper functions. This simplified the main `print_panel` function significantly while maintaining identical output behavior.

## 2026-10-18 - [Complexity Reduction]
**Target:** `watch_session` in `src/cli/commands.py`
**Delta:** Removed manual polling loop and sleep management.
**Summary:** Refactored `watch_session` to use `poll_with_result` from `src.utils.polling`, reducing code duplication and standardizing polling logic across the application.
