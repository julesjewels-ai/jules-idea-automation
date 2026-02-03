# Ockham Refactor Log

## 2024-05-23
- **Target:** `scrape_text` in `src/services/scraper.py`
- **Delta:** Complexity Score 14 -> 3
- **Summary:** Extracted `_fetch_response` and `_extract_text` helpers to separate network I/O and HTML parsing from the main orchestration logic, flattening nested error handling.

## 2024-05-23
- **Target:** `JulesClient` in `src/services/jules.py`
- **Delta:** Error Clarity + Logic Consolidation
- **Summary:** Introduced `_request` helper to centralize API calls and standardized error handling using `JulesApiError` with user-friendly tips, replacing scattered `requests.raise_for_status()` calls.
