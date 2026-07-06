"""Core interfaces and protocols for the Jules Automation Tool."""

from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar

T_Report = TypeVar("T_Report", covariant=True)
T_Report_Contra = TypeVar("T_Report_Contra", contravariant=True)


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def handle(self, event: Any) -> None:
        """Handle an event.

        Args:
        ----
            event: The domain event to handle.

        """
        ...


class EventBus(Protocol):
    """Protocol for the application event bus."""

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
        ----
            event_type: The type of event to subscribe to.
            handler: The handler to call when the event is published.

        """
        ...

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers.

        Args:
        ----
            event: The domain event to publish.

        """
        ...


class CacheProvider(Protocol):
    """Protocol for caching mechanism."""

    def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve a value from the cache.

        Args:
        ----
            key: The unique cache key.

        Returns:
        -------
            The cached value as a dictionary, or None if not found.

        """
        ...

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a value in the cache.

        Args:
        ----
            key: The unique cache key.
            value: The value to cache (must be JSON-serializable).

        """
        ...


class ReportGenerator(Protocol, Generic[T_Report]):
    """Protocol for generating reports."""

    def generate(self, data: dict[str, Any]) -> T_Report:
        """Generate a report from the provided data.

        Args:
        ----
            data: The data to include in the report.

        Returns:
        -------
            The generated report.

        """
        ...


class ReportStorage(Protocol, Generic[T_Report_Contra]):
    """Protocol for storing reports."""

    def save(self, report: T_Report_Contra, identifier: str) -> str:
        """Save a report and return its location.

        Args:
        ----
            report: The report to save.
            identifier: A unique identifier for the report.

        Returns:
        -------
            The location where the report was saved.

        """
        ...
