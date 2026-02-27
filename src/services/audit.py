"""Audit logging implementation for the Jules Automation Tool."""

import json
import logging
from pathlib import Path
from typing import Any

from src.core.interfaces import EventHandler
from src.core.events import DomainEvent
from src.utils.errors import AuditError

logger = logging.getLogger(__name__)


class JsonFileAuditLogger(EventHandler):
    """File-based audit logger implementation."""

    def __init__(self, log_file: str = ".jules_history.jsonl") -> None:
        """Initialize the JSON file audit logger.

        Args:
            log_file: The path to the log file (JSONL format).
        """
        self.log_file = Path(log_file)

        # Ensure parent directory exists if a path with directories is provided
        try:
            if self.log_file.parent and str(self.log_file.parent) != ".":
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Failed to create audit log directory {self.log_file.parent}: {e}")

    def handle(self, event: Any) -> None:
        """Handle an event by logging it to the JSONL file.

        Args:
            event: The domain event to handle.
        """
        if not isinstance(event, DomainEvent):
            logger.debug(f"Audit logger ignored non-DomainEvent: {type(event)}")
            return

        try:
            # We add a generic event_type field for easier querying of the JSONL file
            event_data = event.model_dump()
            event_data["event_type"] = event.__class__.__name__

            # Append as JSON Lines (one JSON object per line)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data) + "\n")

            logger.debug(f"Audit logged event {event.__class__.__name__} to {self.log_file}")
        except Exception as e:
            # We wrap the underlying exception into our application's domain error
            raise AuditError(f"Failed to write audit log to {self.log_file}: {e}") from e
