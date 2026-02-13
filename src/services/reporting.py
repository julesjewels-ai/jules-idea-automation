"""Console reporter implementation using EventBus."""

from typing import Optional

from src.core.events import (
    EventBus,
    WorkflowStarted,
    StepStarted,
    StepCompleted,
    WorkflowCompleted,
    WorkflowFailed
)
from src.utils.reporter import (
    print_workflow_report,
    Spinner,
    Colors
)


class ConsoleReporter:
    """Listens to workflow events and prints to console."""

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._spinner: Optional[Spinner] = None
        self._subscribe()

    def _subscribe(self) -> None:
        """Subscribe to relevant events."""
        self.bus.subscribe(WorkflowStarted, self.on_workflow_started)
        self.bus.subscribe(StepStarted, self.on_step_started)
        self.bus.subscribe(StepCompleted, self.on_step_completed)
        self.bus.subscribe(WorkflowCompleted, self.on_workflow_completed)
        self.bus.subscribe(WorkflowFailed, self.on_workflow_failed)

    def on_workflow_started(self, event: WorkflowStarted) -> None:
        """Handle workflow start."""
        print(f"Processing Idea: {event.idea_title}")
        print(f"Slug: {event.slug}")
        print("-" * 40)

    def on_step_started(self, event: StepStarted) -> None:
        """Handle step start."""
        if self._spinner:
            self._spinner.__exit__(None, None, None)
            self._spinner = None

        self._spinner = Spinner(event.message)
        self._spinner.__enter__()

    def on_step_completed(self, event: StepCompleted) -> None:
        """Handle step completion."""
        if self._spinner:
            self._spinner.success_message = event.message
            self._spinner.__exit__(None, None, None)
            self._spinner = None

            if event.result and isinstance(event.result, dict):
                if 'files_created' in event.result:
                    count = event.result['files_created']
                    print(f"  Created {count} files in single commit")

    def on_workflow_completed(self, event: WorkflowCompleted) -> None:
        """Handle workflow completion."""
        if self._spinner:
            self._spinner.__exit__(None, None, None)
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

    def on_workflow_failed(self, event: WorkflowFailed) -> None:
        """Handle workflow failure."""
        if self._spinner:
            self._spinner.__exit__(Exception, Exception(event.error), None)
            self._spinner = None

        print(f"\n{Colors.FAIL}Workflow Failed: {event.error}{Colors.ENDC}")
        if event.tip:
            print(f"{Colors.YELLOW}Tip: {event.tip}{Colors.ENDC}")
