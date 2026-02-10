"""Tests for the event system."""

from unittest.mock import Mock
import pytest
from src.core.events import LocalEventBus, Event, EventListener

class TestListener(EventListener):
    """Test listener implementation."""
    def __init__(self):
        self.received_events = []

    def on_event(self, event: Event) -> None:
        self.received_events.append(event)

class ErrorListener(EventListener):
    """Listener that raises an error."""
    def on_event(self, event: Event) -> None:
        raise ValueError("Something went wrong")

def test_subscribe_and_publish():
    bus = LocalEventBus()
    listener = TestListener()
    bus.subscribe(listener)

    event = Event(name="test_event", payload={"data": 123})
    bus.publish(event)

    assert len(listener.received_events) == 1
    assert listener.received_events[0] == event
    assert listener.received_events[0].name == "test_event"
    assert listener.received_events[0].payload == {"data": 123}

def test_multiple_listeners():
    bus = LocalEventBus()
    l1 = TestListener()
    l2 = TestListener()
    bus.subscribe(l1)
    bus.subscribe(l2)

    event = Event(name="broadcast")
    bus.publish(event)

    assert len(l1.received_events) == 1
    assert len(l2.received_events) == 1

def test_listener_error_does_not_crash_bus(capsys):
    bus = LocalEventBus()
    l1 = TestListener()
    l2 = ErrorListener()
    l3 = TestListener()

    bus.subscribe(l1)
    bus.subscribe(l2)
    bus.subscribe(l3)

    event = Event(name="error_test")
    bus.publish(event)

    # All listeners should be called, error in l2 should be caught
    assert len(l1.received_events) == 1
    assert len(l3.received_events) == 1

    # Check that error was printed to stderr
    captured = capsys.readouterr()
    assert "Error in event listener" in captured.err
