Target: IdeaWorkflow._prepare_scaffold_files in src/core/workflow.py
Delta: Complexity Score 8 -> 6
Summary: Extracted file validation and formatting logic into `_process_file_entry` helper method, reducing nesting and improving readability.

Target: GeminiClient._generate_content in src/services/gemini.py
Delta: Complexity Score 11 -> 6
Summary: Extracted cache key generation, validation logic, and API call execution into helper methods `_get_cache_key`, `_validate_and_return`, and `_safe_generate`, significantly reducing the complexity of the main generation method.
