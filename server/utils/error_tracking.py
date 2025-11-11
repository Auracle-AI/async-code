"""
Sentry Error Tracking Integration
==================================
Automatic error reporting and performance monitoring.

Author: Claude Code
Date: 2025-11-11
"""

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import os
from typing import Optional


def init_sentry(app=None):
    """
    Initialize Sentry error tracking.

    Args:
        app: Flask application instance (optional)
    """
    sentry_dsn = os.getenv('SENTRY_DSN')
    environment = os.getenv('ENVIRONMENT', 'development')

    if not sentry_dsn:
        print("⚠️  SENTRY_DSN not set - error tracking disabled")
        return

    integrations = [
        FlaskIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ]

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=integrations,
        environment=environment,

        # Performance monitoring
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),

        # Profiling
        profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),

        # Release tracking
        release=os.getenv('GIT_COMMIT_SHA', 'unknown'),

        # Filter sensitive data
        before_send=before_send_filter,
    )

    print(f"✅ Sentry initialized (environment: {environment})")


def before_send_filter(event, hint):
    """
    Filter sensitive data before sending to Sentry.

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        Modified event or None to drop event
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']

        sensitive_headers = [
            'Authorization',
            'X-GitHub-Token',
            'Cookie',
            'X-API-Key'
        ]

        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[REDACTED]'

    # Remove sensitive query parameters
    if 'request' in event and 'query_string' in event['request']:
        query = event['request']['query_string']

        sensitive_params = ['token', 'api_key', 'secret']

        for param in sensitive_params:
            if param in query.lower():
                event['request']['query_string'] = '[REDACTED]'
                break

    return event


def capture_task_error(task_id: int, user_id: str, error: Exception, context: dict = None):
    """
    Capture task execution error with context.

    Args:
        task_id: Task ID
        user_id: User ID
        error: Exception that occurred
        context: Additional context dictionary
    """
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("task_id", task_id)
        scope.set_tag("user_id", user_id)
        scope.set_context("task", {
            "task_id": task_id,
            "user_id": user_id,
            **(context or {})
        })

        sentry_sdk.capture_exception(error)


def capture_api_error(endpoint: str, user_id: Optional[str], error: Exception):
    """
    Capture API error with context.

    Args:
        endpoint: API endpoint
        user_id: User ID (optional)
        error: Exception that occurred
    """
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("endpoint", endpoint)
        if user_id:
            scope.set_tag("user_id", user_id)

        sentry_sdk.capture_exception(error)


# Monitoring decorators
def monitor_performance(operation_name: str):
    """
    Decorator to monitor function performance.

    Usage:
        @monitor_performance("task_execution")
        def execute_task():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op=operation_name, name=func.__name__):
                return func(*args, **kwargs)
        return wrapper
    return decorator
