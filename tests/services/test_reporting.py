"""Tests for ConsoleReporter."""

import pytest
from unittest.mock import Mock, patch
from src.services.reporting import ConsoleReporter
from src.services.bus import LocalEventBus
from src.core.events import (
    WorkflowStarted, StepStarted, StepCompleted, WorkflowCompleted, WorkflowFailed
)
from src.core.models import IdeaResponse, WorkflowResult


@pytest.fixture
def bus():
    return LocalEventBus()


@pytest.fixture
def reporter(bus):
    return ConsoleReporter(bus)


def test_reporter_subscribes(bus):
    reporter = ConsoleReporter(bus)
    # Check internals - not ideal but verifies subscriptions
    assert WorkflowStarted in bus._subscribers
    assert StepStarted in bus._subscribers
    assert StepCompleted in bus._subscribers
    assert WorkflowCompleted in bus._subscribers
    assert WorkflowFailed in bus._subscribers


def test_on_workflow_started(bus, reporter, capsys):
    event = WorkflowStarted(idea_title="My App", slug="my-app")
    bus.publish(event)
    captured = capsys.readouterr()
    assert "Processing Idea: My App" in captured.out
    assert "Slug: my-app" in captured.out


@patch("src.services.reporting.Spinner")
def test_on_step_started(mock_spinner, bus, reporter):
    event = StepStarted(step_name="test", message="Doing work...")
    bus.publish(event)

    mock_spinner.assert_called_with("Doing work...")
    mock_spinner.return_value.__enter__.assert_called_once()


@patch("src.services.reporting.Spinner")
def test_on_step_completed(mock_spinner, bus, reporter):
    # Simulate step started
    spinner_instance = mock_spinner.return_value
    reporter._spinner = spinner_instance

    event = StepCompleted(step_name="test", message="Done!")
    bus.publish(event)

    # Verify success message set on the mock instance
    assert spinner_instance.success_message == "Done!"
    # Verify exit called
    spinner_instance.__exit__.assert_called_once()
    assert reporter._spinner is None


@patch("src.services.reporting.print_workflow_report")
def test_on_workflow_completed(mock_print_report, bus, reporter):
    idea = IdeaResponse(title="T", description="D", slug="s", tech_stack=[], features=[])
    result = WorkflowResult(idea=idea, repo_url="url", session_id="sid", session_url="surl")
    event = WorkflowCompleted(result=result)

    bus.publish(event)

    mock_print_report.assert_called_once()


def test_on_workflow_failed(bus, reporter, capsys):
    event = WorkflowFailed(error="Boom", tip="Fix it")
    bus.publish(event)

    captured = capsys.readouterr()
    assert "Workflow Failed: Boom" in captured.out
    assert "Tip: Fix it" in captured.out
