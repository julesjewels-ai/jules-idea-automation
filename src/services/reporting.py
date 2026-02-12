"""Console reporting service."""

from typing import Optional
from src.core.events import (
    Event,
    WorkflowStarted,
    StepStarted,
    StepCompleted,
    StepFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from src.utils.reporter import (
    Spinner,
    print_workflow_report,
    Colors
)


class ConsoleReporter:
    """Event listener that reports workflow progress to the console."""

    def __init__(self) -> None:
        """Initialize the console reporter."""
        self._spinner: Optional[Spinner] = None

    def handle(self, event: Event) -> None:
        """Handle an incoming event.

        Args:
            event: The event to handle.
        """
        if isinstance(event, WorkflowStarted):
            print(f"Processing Idea: {event.idea_title}")
            print(f"Slug: {event.slug}")
            print("-" * 40)

        elif isinstance(event, StepStarted):
            if self._spinner:
                self._spinner.stop()
            self._spinner = Spinner(event.step_name)
            self._spinner.start()

        elif isinstance(event, StepCompleted):
            if self._spinner:
                # If we have a running spinner, mark it as successful
                self._spinner.succeed()
                self._spinner = None
            else:
                print(f"{Colors.GREEN}✔ {event.step_name}{Colors.ENDC}")

        elif isinstance(event, StepFailed):
            if self._spinner:
                self._spinner.fail(event.error)
                self._spinner = None
            else:
                msg = f"{Colors.FAIL}✖ {event.step_name}: {event.error}"
                print(f"{msg}{Colors.ENDC}")

        elif isinstance(event, WorkflowCompleted):
            # Ensure any lingering spinner is stopped
            if self._spinner:
                self._spinner.stop()
                self._spinner = None

            result = event.result
            print_workflow_report(
                title=result.idea.title,
                slug=result.idea.slug,
                repo_url=result.repo_url,
                session_id=result.session_id,
                session_url=result.session_url,
                pr_url=result.pr_url
            )

        elif isinstance(event, WorkflowFailed):
            if self._spinner:
                self._spinner.fail(event.error)
                self._spinner = None
            else:
                print(
                    f"\n{Colors.FAIL}Workflow Failed: "
                    f"{event.error}{Colors.ENDC}"
                )
