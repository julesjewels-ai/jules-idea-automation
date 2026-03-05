Based on the instructions and memory:

The missing utility feature requested is a data persistence layer using the **Repository pattern**.
Memory specifically mentions:
* `IdeaWorkflow` supports an optional injected `ProjectRepository` dependency (e.g., `JsonProjectRepository`) to persist `WorkflowResult` objects upon completion.
* Domain errors related to data persistence or retrieval must raise the custom `RepositoryError` defined in `src/utils/errors.py`.
* To prevent data corruption during file-based persistence (e.g., `JsonProjectRepository`), use atomic writes by writing to a temporary file via `tempfile.mkstemp` and swapping with `os.replace`.
* Integration tests for the ProjectRepository implementation are located in `tests/integration/test_repository.py`. When using `pytest.fixture` to yield temporary directories or items, explicitly type the return as a `Generator` (e.g., `Generator[str, None, None]`) to satisfy strict mypy checks.
* The CLI's main execution flow in `src/cli/commands.py` (`_execute_and_watch`) acts as the system's dependency container, instantiating and wiring services like `JsonProjectRepository` and `LocalEventBus` into `IdeaWorkflow`.
* The project uses the Repository pattern for data persistence, implemented via Generic Protocols (e.g., `ProjectRepository[T]`) to ensure strict typing of domain models like `WorkflowResult`.

Let's check the current codebase:
1. `ProjectRepository` protocol is missing in `src/core/interfaces.py`.
2. `JsonProjectRepository` is missing in `src/services/repository.py`.
3. `RepositoryError` is missing in `src/utils/errors.py`.
4. `IdeaWorkflow` in `src/core/workflow.py` does not support `repository` parameter and does not persist `WorkflowResult` on completion.
5. `tests/integration/test_repository.py` needs to be created.
6. `src/cli/commands.py` needs to wire `JsonProjectRepository` in `_execute_and_watch`.
