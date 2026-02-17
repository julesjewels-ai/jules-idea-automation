"""Core interfaces and protocols for the application."""

from typing import Protocol, TypeVar, Callable, Any, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class ResiliencePolicy(Protocol):
    """Interface for resilience strategies like retries and circuit breakers."""

    def execute(self,
                operation: Callable[..., T],
                *args: Any,
                **kwargs: Any) -> T:
        """Executes the given operation with the implemented resilience strategy.

        Args:
            operation: The callable to execute.
            *args: Positional arguments for the operation.
            **kwargs: Keyword arguments for the operation.

        Returns:
            The result of the operation.

        Raises:
            Exception: The exception raised by the operation if resilience fails.  # noqa: E501
        """
        ...
