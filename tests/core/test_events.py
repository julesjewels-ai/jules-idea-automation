"""Tests for the event system."""

import pytest
from src.core.interfaces import Event
from src.services.event_bus import LocalEventBus


class MockEvent(Event):
    """Test event."""
    data: str


def test_event_bus_subscribe_publish():
    """Test that the event bus publishes events to subscribers."""
    bus = LocalEventBus()
    received = []

    def handler(event: MockEvent):
        received.append(event.data)

    bus.subscribe(MockEvent, handler)
    bus.publish(MockEvent(data="test"))

    assert len(received) == 1
    assert received[0] == "test"


def test_event_bus_multiple_subscribers():
    """Test multiple subscribers for the same event."""
    bus = LocalEventBus()
    count = 0

    def handler1(event):
        nonlocal count
        count += 1

    def handler2(event):
        nonlocal count
        count += 2

    bus.subscribe(MockEvent, handler1)
    bus.subscribe(MockEvent, handler2)
    bus.publish(MockEvent(data="test"))

    assert count == 3


def test_event_bus_error_handling(caplog):
    """Test that subscriber errors are caught and logged."""
    bus = LocalEventBus()

    def failing_handler(event):
        raise ValueError("Boom")

    bus.subscribe(MockEvent, failing_handler)

    # Should not raise exception
    bus.publish(MockEvent(data="test"))

    # Check if error was logged
    assert "Error handling event MockEvent: Boom" in caplog.text
