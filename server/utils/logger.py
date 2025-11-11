"""
Structured Logging System for Async Code
=========================================
Production-grade logging with structured output, context tracking,
and integration with external log aggregation services.

Author: Claude Code
Date: 2025-11-11
"""

import logging
import sys
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from functools import wraps
import traceback


class StructuredLogger:
    """
    Structured logger with JSON output and context tracking.
    """

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.context = {}

        # Remove existing handlers
        self.logger.handlers = []

        # Add JSON handler for production
        json_handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(context)s'
        )
        json_handler.setFormatter(formatter)
        self.logger.addHandler(json_handler)

    def add_context(self, **kwargs):
        """Add persistent context to all log messages."""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear all context."""
        self.context = {}

    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method with context."""
        log_data = {
            **self.context,
            **kwargs,
            'timestamp': datetime.utcnow().isoformat(),
        }

        getattr(self.logger, level)(message, extra={'context': log_data})

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log('debug', message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log('info', message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log('warning', message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log('error', message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log('critical', message, **kwargs)

    def exception(self, message: str, exc_info=True, **kwargs):
        """Log exception with traceback."""
        if exc_info:
            kwargs['traceback'] = traceback.format_exc()
        self._log('error', message, **kwargs)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logs."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['message'] = record.getMessage()

        # Add context if available
        if hasattr(record, 'context'):
            log_record.update(record.context)

        # Add exception info if available
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def log_execution_time(logger: StructuredLogger):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func.__name__

            logger.info(
                f"Function started",
                function=function_name,
                event="function_start"
            )

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                logger.info(
                    f"Function completed",
                    function=function_name,
                    execution_time=execution_time,
                    event="function_complete"
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                logger.error(
                    f"Function failed",
                    function=function_name,
                    execution_time=execution_time,
                    error=str(e),
                    event="function_error"
                )
                raise

        return wrapper
    return decorator


def log_task_lifecycle(logger: StructuredLogger):
    """Decorator specifically for task execution logging."""
    def decorator(func):
        @wraps(func)
        def wrapper(task_id: int, user_id: str, *args, **kwargs):
            # Add task context
            logger.add_context(
                task_id=task_id,
                user_id=user_id
            )

            logger.info(
                "Task execution started",
                event="task_start"
            )

            start_time = time.time()

            try:
                result = func(task_id, user_id, *args, **kwargs)
                execution_time = time.time() - start_time

                logger.info(
                    "Task execution completed",
                    execution_time=execution_time,
                    event="task_complete"
                )

                logger.clear_context()
                return result

            except Exception as e:
                execution_time = time.time() - start_time

                logger.error(
                    "Task execution failed",
                    execution_time=execution_time,
                    error=str(e),
                    error_type=type(e).__name__,
                    event="task_error"
                )

                logger.clear_context()
                raise

        return wrapper
    return decorator


# Global logger instances
app_logger = StructuredLogger("async_code", level="INFO")
task_logger = StructuredLogger("async_code.tasks", level="INFO")
api_logger = StructuredLogger("async_code.api", level="INFO")
swarm_logger = StructuredLogger("async_code.swarm", level="INFO")


# Flask request logging middleware
class RequestLoggingMiddleware:
    """Middleware to log all HTTP requests."""

    def __init__(self, app, logger: StructuredLogger):
        self.app = app
        self.logger = logger

    def __call__(self, environ, start_response):
        # Extract request info
        method = environ.get('REQUEST_METHOD')
        path = environ.get('PATH_INFO')
        query_string = environ.get('QUERY_STRING', '')
        user_id = environ.get('HTTP_X_USER_ID', 'anonymous')

        start_time = time.time()

        self.logger.info(
            "HTTP request started",
            method=method,
            path=path,
            query_string=query_string,
            user_id=user_id,
            event="http_request_start"
        )

        def custom_start_response(status, response_headers, exc_info=None):
            execution_time = time.time() - start_time
            status_code = int(status.split()[0])

            self.logger.info(
                "HTTP request completed",
                method=method,
                path=path,
                status_code=status_code,
                execution_time=execution_time,
                user_id=user_id,
                event="http_request_complete"
            )

            return start_response(status, response_headers, exc_info)

        return self.app(environ, custom_start_response)


if __name__ == "__main__":
    # Test the logging system
    print("=" * 60)
    print("Structured Logging System Test")
    print("=" * 60)

    # Test basic logging
    app_logger.info("Application started", version="1.0.0", environment="test")

    # Test with context
    app_logger.add_context(request_id="test-123", user_id="user-456")
    app_logger.info("Processing request")
    app_logger.clear_context()

    # Test task logging
    @log_task_lifecycle(task_logger)
    def test_task(task_id: int, user_id: str):
        task_logger.info("Executing task logic")
        time.sleep(0.1)
        return {"status": "success"}

    test_task(123, "user-789")

    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        app_logger.exception("An error occurred", error_context="test")

    print("\n✅ Logging system test complete!")
