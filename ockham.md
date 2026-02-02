# Ockham Refactor Log

## 2024-05-23
- **Target:** `scrape_text` in `src/services/scraper.py`
- **Delta:** Complexity Score 14 -> 3
- **Summary:** Extracted `_fetch_response` and `_extract_text` helpers to separate network I/O and HTML parsing from the main orchestration logic, flattening nested error handling.

## 2026-02-02
- **Target:** `validate_url` in `src/utils/security.py`
- **Delta:** Complexity Score 11 -> 1
- **Summary:** Refactored `validate_url` by extracting scheme validation, hostname checks, IP resolution, and IP safety checks into distinct helper functions, linearizing the orchestration logic.
