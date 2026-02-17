"""Tests for the console reporter."""

from unittest.mock import MagicMock, patch
from src.services.reporting import ConsoleReporter
from src.services.event_bus import LocalEventBus
from src.core.events import StepStarted, StepCompleted, StepProgress


@patch("src.services.reporting.Spinner")
def test_console_reporter_spinner(mock_spinner_cls):
    """Test that the reporter manages the spinner correctly."""
    bus = LocalEventBus()
    reporter = ConsoleReporter(verbose=True)
    reporter.register(bus)

    mock_spinner = MagicMock()
    mock_spinner_cls.return_value = mock_spinner

    # Start step
    bus.publish(StepStarted(step_name="step1", message="Starting..."))

    mock_spinner_cls.assert_called_with("Starting...")
    mock_spinner.__enter__.assert_called_once()

    # Update progress
    bus.publish(StepProgress(step_name="step1", message="Working..."))
    mock_spinner.update.assert_called_with("Working...")

    # Complete step
    bus.publish(StepCompleted(step_name="step1", result="Done"))

    assert mock_spinner.success_message == "Done"
    mock_spinner.__exit__.assert_called()
