Target: GeminiClient._fetch_from_api in src/services/gemini.py
Delta: Complexity Score 8 -> 4
Summary: Extracted response parsing, caching, and validation logic from `_fetch_from_api` into a new `_process_api_response` helper method, reducing the cyclomatic complexity of `_fetch_from_api` by flattening the main execution path.

Target: _normalize_requirements in src/core/workflow.py
Delta: Complexity Score 14 -> 5
Summary: Extracted dictionary and list parsing logic into `_parse_dict_requirement`, `_parse_list_dict_requirement`, and `_parse_list_requirement` helper methods to simplify the `_normalize_requirements` method.

Target: _map_api_error in src/services/gemini.py
Delta: Complexity Score 8 -> 3
Summary: Replaced complex if-elif logic with a configuration dictionary mapping for substring matches to flatten control flow.
