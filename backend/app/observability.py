"""Minimal structured application logging for DocLens."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
import sys
from typing import TextIO


LOGGER_NAME = "doclens"

_EVENT_FIELDS = {
    "request_completed": (
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
    ),
    "query_completed": (
        "request_id",
        "outcome",
        "retrieved_count",
        "retrieved",
    ),
}


class JsonFormatter(logging.Formatter):
    """Format approved application fields as one compact JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        event = record.getMessage()
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "event": event,
        }
        for field in _EVENT_FIELDS.get(event, ()):
            payload[field] = getattr(record, field)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(stream: TextIO | None = None) -> logging.Logger:
    """Configure one stdout JSON handler and return the application logger."""

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(handler.get_name() == "doclens_json" for handler in logger.handlers):
        handler = logging.StreamHandler(stream or sys.stdout)
        handler.set_name("doclens_json")
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger
