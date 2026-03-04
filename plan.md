1. **Define `RepositoryError`**: Add it to `src/utils/errors.py`.
2. **Define `ProjectRepository[T]` Protocol**: Add it to `src/core/interfaces.py`.
3. **Implement `JsonProjectRepository`**: Create `src/services/repository.py` adhering to the `ProjectRepository[T]` protocol using atomic writes (`tempfile.mkstemp` + `os.replace`).
4. **Update `IdeaWorkflow`**: Modify `src/core/workflow.py` to accept an optional `ProjectRepository` in its constructor and persist `WorkflowResult` objects upon completion.
5. **Update CLI commands**: Wire `JsonProjectRepository` in `src/cli/commands.py` inside `_execute_and_watch`.
6. **Integration Test**: Write `tests/integration/test_repository.py` following the memory directives (`Generator` fixture types, etc.).
7. **Quality Gates**: Run `mypy src/ tests/ --strict`, `ruff check src/ tests/`, `pytest tests/` to ensure no regressions and strict type compliance.
8. **Pre-commit Instructions**: Call `pre_commit_instructions` before submitting to ensure all validations pass.
