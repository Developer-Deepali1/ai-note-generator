"""Decorator utilities for logging, validation and error handling."""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

F = TypeVar('F', bound=Callable[..., Any])



def log_execution(logger: logging.Logger | None = None) -> Callable[[F], F]:
    """Log function start/end events."""
    resolved_logger = logger or logging.getLogger(__name__)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            resolved_logger.info('Executing %s', func.__name__)
            result = func(*args, **kwargs)
            resolved_logger.info('Completed %s', func.__name__)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator



def handle_errors(*, default_response: Any = None, logger: logging.Logger | None = None) -> Callable[[F], F]:
    """Catch unhandled errors and optionally return a default response."""
    resolved_logger = logger or logging.getLogger(__name__)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                resolved_logger.exception('Unhandled error in %s: %s', func.__name__, exc)
                if default_response is not None:
                    return default_response
                raise

        return wrapper  # type: ignore[return-value]

    return decorator



def measure_performance(logger: logging.Logger | None = None) -> Callable[[F], F]:
    """Measure function execution time in milliseconds."""
    resolved_logger = logger or logging.getLogger(__name__)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            started = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - started) * 1000
                resolved_logger.info('%s executed in %.2fms', func.__name__, elapsed_ms)

        return wrapper  # type: ignore[return-value]

    return decorator



def validate_request(*, required_fields: tuple[str, ...]) -> Callable[[F], F]:
    """Validate request payload-like dictionaries for required fields."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(payload: dict[str, Any], *args: Any, **kwargs: Any):
            if not isinstance(payload, dict):
                raise ValueError('Payload must be a dictionary.')
            missing = [field for field in required_fields if field not in payload]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
            return func(payload, *args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator



def require_authentication(func: F) -> F:
    """Placeholder authentication decorator for future integration."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]



def rate_limit(*, requests_per_minute: int = 60) -> Callable[[F], F]:
    """Placeholder rate-limiting decorator for future integration."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            _ = requests_per_minute
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
