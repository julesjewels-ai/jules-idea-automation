"""Tests for event system."""

from src.core.events import Event, WorkflowStarted
from src.services.bus import LocalEventBus
from unittest.mock import Mock


class TestEvent(Event):
    """Test event."""
    data: str


def test_event_creation() -> None:
    """Test event creation."""
    event = TestEvent(data="test")
    assert event.data == "test"
    assert event.timestamp is not None


def test_local_event_bus() -> None:
    """Test local event bus."""
    bus = LocalEventBus()
    handler = Mock()

    bus.subscribe(TestEvent, handler)

    event = TestEvent(data="test")
    bus.publish(event)

    handler.assert_called_once_with(event)


def test_local_event_bus_no_subscribers() -> None:
    """Test bus with no subscribers."""
    bus = LocalEventBus()
    event = TestEvent(data="test")
    # Should not raise
    bus.publish(event)


def test_local_event_bus_multiple_handlers() -> None:
    """Test multiple handlers."""
    bus = LocalEventBus()
    h1 = Mock()
    h2 = Mock()

    bus.subscribe(TestEvent, h1)
    bus.subscribe(TestEvent, h2)

    event = TestEvent(data="test")
    bus.publish(event)

    h1.assert_called_once_with(event)
    h2.assert_called_once_with(event)


def test_local_event_bus_specific_events() -> None:
    """Test subscription to specific events."""
    bus = LocalEventBus()
    h1 = Mock()
    h2 = Mock()

    bus.subscribe(TestEvent, h1)
    bus.subscribe(WorkflowStarted, h2)

    e1 = TestEvent(data="test")
    e2 = WorkflowStarted(idea_title="T", slug="s")

    bus.publish(e1)
    h1.assert_called_once_with(e1)
    h2.assert_not_called()

    h1.reset_mock()
    bus.publish(e2)
    h1.assert_not_called()
    h2.assert_called_once_with(e2)
