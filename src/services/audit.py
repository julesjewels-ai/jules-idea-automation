"""Audit logger implementation for the Jules Automation Tool.

Persists domain events to a local JSONL file for auditing and troubleshooting.
"""

import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from src.core.interfaces import EventHandler
from src.core.events import BaseDomainEvent


logger = logging.getLogger(__name__)


class JsonFileAuditLogger(EventHandler):
    """Event handler that logs events to a JSONL file."""

    def __init__(self, filepath: str = ".jules_history.jsonl") -> None:
        """Initialize the audit logger.

        Args:
            filepath: The path to the audit log file.
        """
        self.filepath = Path(filepath)

    def handle(self, event: Any) -> None:
        """Handle a domain event by appending it to the log file.

        Args:
            event: The domain event to log.
        """
        if not isinstance(event, BaseDomainEvent):
            logger.warning(f"Ignoring non-domain event: {type(event)}")
            return

        try:
            event_data = event.model_dump()

            # Serialize datetime objects to ISO format
            if 'timestamp' in event_data and isinstance(event_data['timestamp'], datetime):
                event_data['timestamp'] = event_data['timestamp'].isoformat()

            with self.filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
