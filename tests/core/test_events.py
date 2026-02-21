"""Tests for the event system."""

from unittest.mock import Mock
from src.core.interfaces import Event
from src.core.bus import LocalEventBus


class CustomEvent(Event):
    """A custom event for testing."""
    payload: str


class SubEvent(CustomEvent):
    """A sub-event for testing inheritance."""
    pass


def test_bus_subscribe_and_publish():
    """Test that subscribers receive published events."""
    bus = LocalEventBus()
    handler = Mock()
    handler.handle = Mock()

    bus.subscribe(CustomEvent, handler)

    event = CustomEvent(payload="test")
    bus.publish(event)

    handler.handle.assert_called_once_with(event)


def test_bus_inheritance_handling():
    """Test that subscribers to parent classes receive subclass events."""
    bus = LocalEventBus()

    event_handler = Mock()
    event_handler.handle = Mock()

    custom_handler = Mock()
    custom_handler.handle = Mock()

    bus.subscribe(Event, event_handler)
    bus.subscribe(CustomEvent, custom_handler)

    event = SubEvent(payload="sub")
    bus.publish(event)

    # event_handler subscribed to Event should receive SubEvent (grandchild)
    event_handler.handle.assert_called_once_with(event)

    # custom_handler subscribed to CustomEvent should receive SubEvent (child)
    custom_handler.handle.assert_called_once_with(event)


def test_bus_no_subscribers():
    """Test publishing with no subscribers."""
    bus = LocalEventBus()
    event = CustomEvent(payload="test")
    # Should not raise error
    bus.publish(event)


def test_multiple_subscribers():
    """Test multiple subscribers for the same event."""
    bus = LocalEventBus()
    handler1 = Mock()
    handler1.handle = Mock()
    handler2 = Mock()
    handler2.handle = Mock()

    bus.subscribe(CustomEvent, handler1)
    bus.subscribe(CustomEvent, handler2)

    event = CustomEvent(payload="test")
    bus.publish(event)

    handler1.handle.assert_called_once_with(event)
    handler2.handle.assert_called_once_with(event)
