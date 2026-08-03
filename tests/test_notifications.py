"""Tests for notification services."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.core.events import WorkflowCompleted, WorkflowStarted
from src.services.notifications import WebhookNotificationProvider, WorkflowNotificationHandler
from src.utils.errors import NotificationError


def test_webhook_provider_send_success() -> None:
    """Test successful webhook notification sending."""
    provider = WebhookNotificationProvider("http://example.com/webhook")

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        provider.send(message="Test message", title="Test Title")

        mock_post.assert_called_once_with(
            "http://example.com/webhook", json={"text": "Test Title\nTest message"}, timeout=10
        )


def test_webhook_provider_send_failure() -> None:
    """Test webhook notification sending failure."""
    provider = WebhookNotificationProvider("http://example.com/webhook")

    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("API Error")

        with pytest.raises(NotificationError) as exc_info:
            provider.send(message="Test message")

        assert "API Error" in str(exc_info.value)


def test_workflow_notification_handler_started() -> None:
    """Test handler for WorkflowStarted event."""
    mock_provider = MagicMock()
    handler = WorkflowNotificationHandler(mock_provider)

    event = WorkflowStarted(event_id="evt_123", idea_title="Test Idea", idea_slug="test-idea", category="productivity")

    handler.handle(event)

    mock_provider.send.assert_called_once_with(
        message="Slug: test-idea\nCategory: productivity", title="🚀 Workflow Started: Test Idea"
    )


def test_workflow_notification_handler_completed() -> None:
    """Test handler for WorkflowCompleted event."""
    mock_provider = MagicMock()
    handler = WorkflowNotificationHandler(mock_provider)

    event = WorkflowCompleted(
        event_id="evt_123",
        idea_title="Test Idea",
        idea_slug="test-idea",
        repo_url="https://github.com/user/test-idea",
        session_url="https://jules.google.com/session/123",
    )

    handler.handle(event)

    mock_provider.send.assert_called_once_with(
        message="Slug: test-idea\nRepository: https://github.com/user/test-idea\nJules Session: https://jules.google.com/session/123",
        title="✅ Workflow Completed: Test Idea",
    )


def test_workflow_notification_handler_handles_error() -> None:
    """Test handler gracefully handles NotificationError."""
    mock_provider = MagicMock()
    mock_provider.send.side_effect = NotificationError("Failed")
    handler = WorkflowNotificationHandler(mock_provider)

    event = WorkflowStarted(event_id="evt_123", idea_title="Test Idea", idea_slug="test-idea")

    # Should not raise exception
    handler.handle(event)
    mock_provider.send.assert_called_once()
