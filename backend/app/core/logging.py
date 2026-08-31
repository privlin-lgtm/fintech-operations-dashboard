import json
import logging
import sys
from datetime import UTC, datetime

_EXTRA_FIELDS = ("request_id", "path", "method", "status_code", "duration_ms")


class JsonFormatter(logging.Formatter):
    """One JSON object per line — easy to ship to any log aggregator without
    a parser that understands Python's default log format."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _EXTRA_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(*, debug: bool) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Uvicorn's own loggers otherwise print in its default (non-JSON) format,
    # which defeats the point of having one consistent log shape.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False
