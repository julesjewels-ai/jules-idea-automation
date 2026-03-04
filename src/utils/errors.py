"""Application-specific exceptions."""

from __future__ import annotations


class AppError(Exception):
    """Base class for application errors."""

    def __init__(self, message: str, tip: str | None = None):
        super().__init__(message)
        self.tip = tip


class ConfigurationError(AppError):
    """Raised when configuration is missing or invalid."""

    pass


class GenerationError(AppError):
    """Raised when GenAI generation fails or returns invalid output."""

    pass


class JulesApiError(AppError):
    """Raised when the Jules API returns an error."""

    pass


class EventBusError(AppError):
    """Raised when an error occurs in the EventBus."""

    pass


class AuditError(AppError):
    """Raised when an error occurs during audit logging."""

    pass


class RepositoryError(AppError):
    """Raised when a data persistence or retrieval error occurs."""

    pass
