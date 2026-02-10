"""Console reporting service implementation."""

from typing import Optional
from src.core.events import Event
from src.utils.reporter import (
    print_workflow_report,
    Colors,
    Spinner
)


class ConsoleReporter:
    """Event listener that reports workflow progress to the console."""

    def __init__(self, verbose: bool = True) -> None:
        """Initialize the reporter."""
        self.verbose = verbose
        self._current_spinner: Optional[Spinner] = None

    def on_event(self, event: Event) -> None:
        """Handle events and update console output."""
        if not self.verbose:
            return

        method_name = f"_handle_{event.name}"
        handler = getattr(self, method_name, self._handle_default)
        handler(event)

    def _handle_default(self, event: Event) -> None:
        """Default handler for unhandled events."""
        pass

    def _start_spinner(self, message: str) -> None:
        if self._current_spinner:
            self._stop_spinner()
        self._current_spinner = Spinner(message)
        self._current_spinner.__enter__()

    def _stop_spinner(
        self,
        success: bool = True,
        message: Optional[str] = None
    ) -> None:
        if self._current_spinner:
            if message and success:
                self._current_spinner.success_message = message

            # If not success, simulate an exception for the spinner to show 'X'
            exc_type = Exception if not success else None
            exc_val = Exception(message) if not success else None

            # We need to pass 3 args to __exit__
            self._current_spinner.__exit__(exc_type, exc_val, None)
            self._current_spinner = None

    def _handle_workflow_started(self, event: Event) -> None:
        print(f"Processing Idea: {event.payload.get('title')}")
        print(f"Slug: {event.payload.get('slug')}")
        print("-" * 40)

    def _handle_step_started(self, event: Event) -> None:
        message = event.payload.get("message", "Processing...")
        self._start_spinner(message)

    def _handle_step_completed(self, event: Event) -> None:
        message = event.payload.get("message")
        self._stop_spinner(success=True, message=message)

        # If there are additional details to print after the spinner
        details = event.payload.get("details")
        if details:
            print(details)

    def _handle_repo_created(self, event: Event) -> None:
        # This might be handled by step_started/completed
        pass

    def _handle_scaffold_generated(self, event: Event) -> None:
        files_count = event.payload.get("files_count")
        if files_count:
            print(f"  Created {files_count} files in single commit")

    def _handle_session_created(self, event: Event) -> None:
        pass

    def _handle_workflow_completed(self, event: Event) -> None:
        # Stop any running spinner
        if self._current_spinner:
            self._stop_spinner(success=True)

        result = event.payload.get("result")
        if result:
            print_workflow_report(
                title=result.get("idea", {}).get("title", "Unknown"),
                slug=result.get("idea", {}).get("slug", "unknown"),
                repo_url=result.get("repo_url", ""),
                session_id=result.get("session_id"),
                session_url=result.get("session_url"),
                pr_url=result.get("pr_url")
            )

    def _handle_workflow_failed(self, event: Event) -> None:
        error = event.payload.get("error", "Unknown error")
        self._stop_spinner(success=False, message=str(error))
        print(f"\n{Colors.FAIL}Workflow Failed:{Colors.ENDC} {error}")
