# Ockham Refactor Log

## 2024-05-23
- **Target:** `scrape_text` in `src/services/scraper.py`
- **Delta:** Complexity Score 14 -> 3
- **Summary:** Extracted `_fetch_response` and `_extract_text` helpers to separate network I/O and HTML parsing from the main orchestration logic, flattening nested error handling.

## 2024-05-24
- **Target:** `IdeaWorkflow._generate_scaffold` in `src/core/workflow.py`
- **Delta:** Complexity Score 10 -> 6
- **Summary:** Extracted file preparation logic into `_prepare_files_for_commit` helper method, reducing nesting and improving readability.
