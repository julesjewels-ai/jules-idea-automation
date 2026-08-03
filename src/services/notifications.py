"""Notification services for the Jules Automation Tool."""

from __future__ import annotations

import logging
from typing import Any

import requests

from src.core.events import WorkflowCompleted, WorkflowStarted
from src.core.interfaces import EventHandler, NotificationProvider
from src.utils.errors import NotificationError

logger = logging.getLogger(__name__)


class WebhookNotificationProvider(NotificationProvider):
    """Notification provider that sends messages to a webhook URL."""

    def __init__(self, webhook_url: str) -> None:
        """Initialize the webhook notification provider.

        Args:
        ----
            webhook_url: The URL to send webhook payloads to.

        """
        self.webhook_url = webhook_url

    def send(self, message: str, title: str | None = None) -> None:
        """Send a notification to the webhook URL.

        Args:
        ----
            message: The main content of the notification.
            title: An optional title for the notification.

        Raises:
        ------
            NotificationError: If the webhook request fails.

        """
        payload = {"text": f"{title}\n{message}" if title else message}
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to send webhook notification: {e}")
            raise NotificationError(f"Failed to send webhook notification: {e}") from e


class WorkflowNotificationHandler(EventHandler):
    """Handles workflow events and sends notifications."""

    def __init__(self, provider: NotificationProvider) -> None:
        """Initialize the workflow notification handler.

        Args:
        ----
            provider: The notification provider to use.

        """
        self.provider = provider

    def handle(self, event: Any) -> None:
        """Handle an event and send a notification.

        Args:
        ----
            event: The domain event to handle.

        """
        try:
            if isinstance(event, WorkflowStarted):
                title = f"🚀 Workflow Started: {event.idea_title}"
                message = f"Slug: {event.idea_slug}\nCategory: {getattr(event, 'category', None) or 'None'}"
                self.provider.send(message=message, title=title)
            elif isinstance(event, WorkflowCompleted):
                title = f"✅ Workflow Completed: {event.idea_title}"
                message = f"Slug: {event.idea_slug}\nRepository: {event.repo_url}"

                if event.session_url:
                    message += f"\nJules Session: {event.session_url}"
                self.provider.send(message=message, title=title)
        except NotificationError as e:
            logger.warning(f"Notification handler failed: {e}")
