Target: GeminiClient._fetch_from_api in src/services/gemini.py
Delta: Complexity Score 8 -> 4
Summary: Extracted response parsing, caching, and validation logic from `_fetch_from_api` into a new `_process_api_response` helper method, reducing the cyclomatic complexity of `_fetch_from_api` by flattening the main execution path.
