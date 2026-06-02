"""Structured JSON logging utilities for backend services."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.constants import DEFAULT_LOG_LEVEL


class JSONFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        if hasattr(record, 'request_id'):
            payload['request_id'] = record.request_id
        if hasattr(record, 'session_id'):
            payload['session_id'] = record.session_id

        for key, value in record.__dict__.items():
            if key.startswith('_') or key in payload or key in _RESERVED_LOG_RECORD_FIELDS:
                continue
            if _is_json_serializable(value):
                payload[key] = value
            else:
                payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


class StructuredLogger:
    """Wrapper around :class:`logging.Logger` with context support."""

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None) -> None:
        self._logger = logger
        self._context = context or {}

    def bind(self, **context: Any) -> 'StructuredLogger':
        """Return a child logger wrapper with merged context."""
        merged = {**self._context, **context}
        return StructuredLogger(self._logger, merged)

    def debug(self, message: str, **fields: Any) -> None:
        self._log(logging.DEBUG, message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._log(logging.INFO, message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._log(logging.WARNING, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, **fields)

    def exception(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, exc_info=True, **fields)

    def _log(self, level: int, message: str, exc_info: bool = False, **fields: Any) -> None:
        extras = {**self._context, **fields}
        self._logger.log(level, message, exc_info=exc_info, extra=extras)


def setup_logging(
    name: str = 'ai_note_generator',
    level: str | int = DEFAULT_LOG_LEVEL,
    *,
    log_file: str | None = None,
    enable_console: bool = True,
) -> StructuredLogger:
    """Configure a logger with JSON formatters for console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = JSONFormatter()
    logger.handlers.clear()

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return StructuredLogger(logger)


def get_logger(name: str = 'ai_note_generator', **context: Any) -> StructuredLogger:
    """Get a configured structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logging(name=name).bind(**context)
    return StructuredLogger(logger).bind(**context)


def _is_json_serializable(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


_RESERVED_LOG_RECORD_FIELDS = {
    'name',
    'msg',
    'args',
    'levelname',
    'levelno',
    'pathname',
    'filename',
    'module',
    'exc_info',
    'exc_text',
    'stack_info',
    'lineno',
    'funcName',
    'created',
    'msecs',
    'relativeCreated',
    'thread',
    'threadName',
    'processName',
    'process',
    'message',
    'asctime',
}
