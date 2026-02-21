"""Console reporter service."""

from src.core.interfaces import Event, EventBus
from src.core.events import (
    WorkflowStarted,
    RepoCreated,
    ScaffoldGenerated,
    SessionWaitStarted,
    SessionCreated,
    WorkflowCompleted,
    WorkflowFailed,
    StepStarted,
    StepCompleted
)
from src.utils.reporter import (
    print_workflow_report,
    Colors,
    print_header
)


class ConsoleReporter:
    """Handles workflow events and prints to console."""

    def __init__(self, bus: EventBus) -> None:
        """Initialize the reporter and subscribe to events."""
        self.bus = bus
        self._subscribe_all()

    def _subscribe_all(self) -> None:
        """Subscribe to all relevant events."""
        self.bus.subscribe(WorkflowStarted, self)
        self.bus.subscribe(RepoCreated, self)
        self.bus.subscribe(ScaffoldGenerated, self)
        self.bus.subscribe(SessionWaitStarted, self)
        self.bus.subscribe(SessionCreated, self)
        self.bus.subscribe(WorkflowCompleted, self)
        self.bus.subscribe(WorkflowFailed, self)
        self.bus.subscribe(StepStarted, self)
        self.bus.subscribe(StepCompleted, self)

    def handle(self, event: Event) -> None:
        """Handle incoming events."""
        # Dispatch to specific handler methods based on event type
        if isinstance(event, WorkflowStarted):
            self._on_workflow_started(event)
        elif isinstance(event, RepoCreated):
            self._on_repo_created(event)
        elif isinstance(event, ScaffoldGenerated):
            self._on_scaffold_generated(event)
        elif isinstance(event, SessionWaitStarted):
            self._on_session_wait_started(event)
        elif isinstance(event, SessionCreated):
            self._on_session_created(event)
        elif isinstance(event, WorkflowCompleted):
            self._on_workflow_completed(event)
        elif isinstance(event, WorkflowFailed):
            self._on_workflow_failed(event)
        elif isinstance(event, StepStarted):
            self._on_step_started(event)
        elif isinstance(event, StepCompleted):
            self._on_step_completed(event)

    def _on_workflow_started(self, event: WorkflowStarted) -> None:
        print_header("🚀 STARTING WORKFLOW")
        print(f"{Colors.BOLD}Processing Idea:{Colors.ENDC} {event.idea.title}")
        print(f"{Colors.BOLD}Slug:           {Colors.ENDC} {event.idea.slug}")
        print("-" * 50)

    def _on_repo_created(self, event: RepoCreated) -> None:
        print(f"{Colors.GREEN}✓{Colors.ENDC} GitHub repository created: "
              f"{Colors.UNDERLINE}{event.repo_url}{Colors.ENDC}")

    def _on_scaffold_generated(self, event: ScaffoldGenerated) -> None:
        print(f"{Colors.GREEN}✓{Colors.ENDC} Generated {event.files_count} files for MVP scaffold")

    def _on_session_wait_started(self, event: SessionWaitStarted) -> None:
        print(f"{Colors.CYAN}ℹ{Colors.ENDC} Waiting for Jules to index repository (timeout: {event.timeout}s)...")

    def _on_session_created(self, event: SessionCreated) -> None:
        print(f"{Colors.GREEN}✓{Colors.ENDC} Jules session created: "
              f"{Colors.UNDERLINE}{event.session_url}{Colors.ENDC}")

    def _on_workflow_completed(self, event: WorkflowCompleted) -> None:
        print_workflow_report(
            title=event.result.idea.title,
            slug=event.result.idea.slug,
            repo_url=event.result.repo_url,
            session_id=event.result.session_id,
            session_url=event.result.session_url,
            pr_url=event.result.pr_url
        )

    def _on_workflow_failed(self, event: WorkflowFailed) -> None:
        print(f"\n{Colors.FAIL}✖ WORKFLOW FAILED{Colors.ENDC}")
        print(f"  Error: {event.error}")
        if event.step_name:
            print(f"  Step:  {event.step_name}")

    def _on_step_started(self, event: StepStarted) -> None:
        # Optional: could use Spinner here if desired
        print(f"{Colors.BLUE}→{Colors.ENDC} {event.description}...")

    def _on_step_completed(self, event: StepCompleted) -> None:
        pass  # Handled by specific events mostly
