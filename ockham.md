# Ockham Refactor Log

## 2024-05-23
- **Target:** `scrape_text` in `src/services/scraper.py`
- **Delta:** Complexity Score 14 -> 3
- **Summary:** Extracted `_fetch_response` and `_extract_text` helpers to separate network I/O and HTML parsing from the main orchestration logic, flattening nested error handling.

## 2026-02-02
- **Target:** `GeminiClient` in `src/services/gemini.py`
- **Delta:** Consolidated 3 repetitive API call blocks into 1 helper.
- **Summary:** Extracted `_generate_content` to standardize Gemini API interactions and error handling. Added missing unit tests (`tests/services/test_gemini.py`) to ensure safety.
