"""Console reporter service."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from src.core.interfaces import EventBus
from src.core.events import (
    WorkflowStarted,
    StepStarted,
    StepCompleted,
    StepFailed,
    StepProgress,
    RepoCreated,
    ScaffoldGenerated,
    JulesSessionCreated,
    WorkflowCompleted,
    WorkflowFailed,
)
from src.utils.reporter import (
    print_workflow_report,
    print_idea_summary,
    Spinner,
    Colors
)

if TYPE_CHECKING:
    pass


class ConsoleReporter:
    """Reporter that listens to events and updates the console."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self._spinner: Optional[Spinner] = None
        self._current_step: Optional[str] = None

    def handle_workflow_started(self, event: WorkflowStarted) -> None:
        if self.verbose:
            print_idea_summary(event.idea.model_dump())

    def handle_step_started(self, event: StepStarted) -> None:
        if not self.verbose:
            return

        # Stop previous spinner if exists (shouldn't happen in normal flow)
        if self._spinner:
            self._spinner.__exit__(None, None, None)

        self._spinner = Spinner(event.message)
        self._spinner.__enter__()  # Manually start spinner thread

        self._current_step = event.step_name

    def handle_step_completed(self, event: StepCompleted) -> None:
        if not self.verbose or not self._spinner:
            return

        self._spinner.success_message = event.result
        self._spinner.__exit__(None, None, None)
        self._spinner = None
        self._current_step = None

    def handle_step_failed(self, event: StepFailed) -> None:
        if not self.verbose or not self._spinner:
            return

        self._spinner.message = event.error
        # Simulate exception to make spinner show fail symbol
        self._spinner.__exit__(Exception, Exception(event.error), None)
        self._spinner = None
        self._current_step = None

    def handle_step_progress(self, event: StepProgress) -> None:
        if not self.verbose or not self._spinner:
            return

        if self._current_step == event.step_name:
            self._spinner.update(event.message)

    def handle_repo_created(self, event: RepoCreated) -> None:
        pass

    def handle_scaffold_generated(self, event: ScaffoldGenerated) -> None:
        pass

    def handle_jules_session_created(self, event: JulesSessionCreated) -> None:
        pass

    def handle_workflow_completed(self, event: WorkflowCompleted) -> None:
        if self.verbose:
            print_workflow_report(
                title=event.result.idea.title,
                slug=event.result.idea.slug,
                repo_url=event.result.repo_url,
                session_id=event.result.session_id,
                session_url=event.result.session_url,
                pr_url=event.result.pr_url
            )

    def handle_workflow_failed(self, event: WorkflowFailed) -> None:
        if self.verbose:
            print(f"\n{Colors.FAIL}Workflow Failed: {event.error}{Colors.ENDC}")

    def register(self, bus: EventBus) -> None:
        """Register handlers with the event bus."""
        bus.subscribe(WorkflowStarted, self.handle_workflow_started)
        bus.subscribe(StepStarted, self.handle_step_started)
        bus.subscribe(StepCompleted, self.handle_step_completed)
        bus.subscribe(StepFailed, self.handle_step_failed)
        bus.subscribe(StepProgress, self.handle_step_progress)
        bus.subscribe(RepoCreated, self.handle_repo_created)
        bus.subscribe(ScaffoldGenerated, self.handle_scaffold_generated)
        bus.subscribe(
            JulesSessionCreated,
            self.handle_jules_session_created
        )
        bus.subscribe(WorkflowCompleted, self.handle_workflow_completed)
        bus.subscribe(WorkflowFailed, self.handle_workflow_failed)
