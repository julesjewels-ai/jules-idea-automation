## 2025-05-26 - [Dead Code Removal] **Observation:** Found `tool.py` referencing non-existent modules (`src.jules_client`) and duplicate/transitional top-level service files (`src/gemini_client.py`, etc.) that were superseded by `src/services/`. This created confusion and potential security risks (`src/scraper.py` lacked SSRF protection). **Action:** Deleted `tool.py`, `src/gemini_client.py`, `src/github_client.py`, and `src/scraper.py`. Verified no usages in active codebase via grep and tests.

## 2026-01-28 - [Complexity Reduction]
**Target:** `print_panel` in `src/utils/reporter.py`
**Delta:** Complexity Score 13 -> 3
**Summary:** Extracted border creation and text wrapping logic into `_create_top_border` and `_wrap_content` helper functions. This simplified the main `print_panel` function significantly while maintaining identical output behavior.

## 2026-02-04 - [Duplication Removal]
**Target:** `GeminiClient` in `src/services/gemini.py`
**Observation:** `generate_idea`, `extract_idea_from_text`, and `generate_project_scaffold` contained identical logic for API call configuration, error handling, and JSON parsing.
**Action:** Extracted `_generate_content` helper method. Reduced code duplication and enforced consistent error handling (DRY).
