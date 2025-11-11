"""
Rate Limiting and Quotas
=========================
Prevent abuse and manage user quotas.

Author: Claude Code
Date: 2025-11-11
"""

from flask import request, jsonify
from functools import wraps
import redis
import time
from typing import Optional, Callable
from datetime import datetime, timedelta
from utils.logger import api_logger
import os


# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=1,  # Use separate DB for rate limiting
    decode_responses=True
)


class UserTier:
    """User tier definitions with quotas."""

    FREE = {
        'name': 'free',
        'tasks_per_day': 10,
        'tasks_per_hour': 5,
        'claude_flow_tasks_per_day': 2,
        'max_concurrent_tasks': 1,
        'api_rate_limit': 60,  # requests per minute
    }

    PRO = {
        'name': 'pro',
        'tasks_per_day': 100,
        'tasks_per_hour': 20,
        'claude_flow_tasks_per_day': 20,
        'max_concurrent_tasks': 5,
        'api_rate_limit': 300,
    }

    ENTERPRISE = {
        'name': 'enterprise',
        'tasks_per_day': 1000,
        'tasks_per_hour': 100,
        'claude_flow_tasks_per_day': 200,
        'max_concurrent_tasks': 20,
        'api_rate_limit': 1000,
    }


def get_user_tier(user_id: str) -> dict:
    """
    Get user tier from database.

    Args:
        user_id: User identifier

    Returns:
        User tier configuration
    """
    # In production, fetch from database
    # For now, default to FREE tier
    return UserTier.FREE


def rate_limit(
    limit: int = 60,
    window: int = 60,
    key_func: Optional[Callable] = None
):
    """
    Rate limiting decorator using token bucket algorithm.

    Args:
        limit: Maximum requests allowed in window
        window: Time window in seconds
        key_func: Function to generate rate limit key (defaults to user_id)

    Usage:
        @app.route('/api/endpoint')
        @rate_limit(limit=10, window=60)
        def my_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get rate limit key
            if key_func:
                key = key_func()
            else:
                user_id = request.headers.get('X-User-ID', 'anonymous')
                key = f"rate_limit:{user_id}:{f.__name__}"

            try:
                # Get current count
                current = redis_client.get(key)

                if current is None:
                    # First request in window
                    redis_client.setex(key, window, 1)
                    remaining = limit - 1
                else:
                    current = int(current)

                    if current >= limit:
                        # Rate limit exceeded
                        ttl = redis_client.ttl(key)

                        api_logger.warning(
                            "Rate limit exceeded",
                            user_id=user_id,
                            endpoint=f.__name__,
                            limit=limit,
                            window=window,
                            event="rate_limit_exceeded"
                        )

                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'limit': limit,
                            'window': window,
                            'retry_after': ttl
                        }), 429

                    # Increment counter
                    redis_client.incr(key)
                    remaining = limit - current - 1

                # Add rate limit headers
                response = f(*args, **kwargs)

                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(limit)
                    response.headers['X-RateLimit-Remaining'] = str(remaining)
                    response.headers['X-RateLimit-Reset'] = str(
                        int(time.time()) + redis_client.ttl(key)
                    )

                return response

            except redis.RedisError as e:
                # If Redis fails, allow request but log error
                api_logger.error(
                    "Rate limiter Redis error",
                    error=str(e),
                    event="rate_limiter_error"
                )
                return f(*args, **kwargs)

        return wrapped
    return decorator


def check_quota(quota_type: str, model: str = None):
    """
    Check if user has quota remaining.

    Args:
        quota_type: Type of quota ('tasks_per_day', 'tasks_per_hour', etc.)
        model: Optional model type ('claude-flow' for special limits)

    Usage:
        @app.route('/start-task')
        @check_quota('tasks_per_day', model='claude-flow')
        def start_task():
            pass
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = request.headers.get('X-User-ID')

            if not user_id:
                return jsonify({'error': 'User ID required'}), 400

            # Get user tier
            tier = get_user_tier(user_id)

            # Special handling for claude-flow
            if model == 'claude-flow':
                quota_key = 'claude_flow_tasks_per_day'
                quota_limit = tier[quota_key]
                window = 86400  # 24 hours
            else:
                quota_limit = tier[quota_type]

                # Determine window
                if 'per_day' in quota_type:
                    window = 86400
                elif 'per_hour' in quota_type:
                    window = 3600
                else:
                    window = 60

            # Check quota
            key = f"quota:{user_id}:{quota_type}"

            try:
                current = redis_client.get(key)

                if current is None:
                    # First usage
                    redis_client.setex(key, window, 1)
                    remaining = quota_limit - 1
                else:
                    current = int(current)

                    if current >= quota_limit:
                        # Quota exceeded
                        ttl = redis_client.ttl(key)

                        api_logger.warning(
                            "Quota exceeded",
                            user_id=user_id,
                            quota_type=quota_type,
                            limit=quota_limit,
                            tier=tier['name'],
                            event="quota_exceeded"
                        )

                        return jsonify({
                            'error': 'Quota exceeded',
                            'quota_type': quota_type,
                            'limit': quota_limit,
                            'tier': tier['name'],
                            'reset_in_seconds': ttl,
                            'upgrade_url': '/pricing'
                        }), 429

                    redis_client.incr(key)
                    remaining = quota_limit - current - 1

                api_logger.info(
                    "Quota check passed",
                    user_id=user_id,
                    quota_type=quota_type,
                    remaining=remaining,
                    limit=quota_limit,
                    event="quota_check"
                )

                # Proceed with request
                return f(*args, **kwargs)

            except redis.RedisError as e:
                # If Redis fails, allow request but log error
                api_logger.error(
                    "Quota check Redis error",
                    error=str(e),
                    event="quota_check_error"
                )
                return f(*args, **kwargs)

        return wrapped
    return decorator


def check_concurrent_tasks(max_concurrent: Optional[int] = None):
    """
    Check if user has too many concurrent tasks running.

    Args:
        max_concurrent: Maximum concurrent tasks (uses tier limit if not specified)
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = request.headers.get('X-User-ID')

            if not user_id:
                return jsonify({'error': 'User ID required'}), 400

            # Get user tier
            tier = get_user_tier(user_id)
            limit = max_concurrent or tier['max_concurrent_tasks']

            # Check running tasks
            key = f"concurrent_tasks:{user_id}"

            try:
                current = int(redis_client.get(key) or 0)

                if current >= limit:
                    api_logger.warning(
                        "Concurrent task limit exceeded",
                        user_id=user_id,
                        current=current,
                        limit=limit,
                        event="concurrent_limit_exceeded"
                    )

                    return jsonify({
                        'error': 'Too many concurrent tasks',
                        'current': current,
                        'limit': limit,
                        'message': 'Please wait for existing tasks to complete'
                    }), 429

                # Increment concurrent counter
                redis_client.incr(key)

                # Call wrapped function
                response = f(*args, **kwargs)

                # Decrement counter on completion (in ideal scenario)
                # Note: This won't work for async tasks - need callback
                # redis_client.decr(key)

                return response

            except redis.RedisError as e:
                api_logger.error(
                    "Concurrent task check error",
                    error=str(e),
                    event="concurrent_check_error"
                )
                return f(*args, **kwargs)

        return wrapped
    return decorator


def decrement_concurrent_tasks(user_id: str):
    """
    Decrement concurrent task counter.
    Should be called when task completes.

    Args:
        user_id: User identifier
    """
    key = f"concurrent_tasks:{user_id}"

    try:
        current = int(redis_client.get(key) or 0)
        if current > 0:
            redis_client.decr(key)

            api_logger.info(
                "Decremented concurrent task counter",
                user_id=user_id,
                new_count=current - 1,
                event="concurrent_task_decrement"
            )

    except redis.RedisError as e:
        api_logger.error(
            "Failed to decrement concurrent tasks",
            user_id=user_id,
            error=str(e),
            event="concurrent_decrement_error"
        )


def get_user_usage_stats(user_id: str) -> dict:
    """
    Get current usage statistics for user.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with usage stats
    """
    tier = get_user_tier(user_id)

    stats = {
        'tier': tier['name'],
        'limits': tier,
        'current_usage': {}
    }

    # Get current usage from Redis
    for quota_type in ['tasks_per_day', 'tasks_per_hour', 'claude_flow_tasks_per_day']:
        key = f"quota:{user_id}:{quota_type}"
        current = int(redis_client.get(key) or 0)
        limit = tier[quota_type]
        ttl = redis_client.ttl(key)

        stats['current_usage'][quota_type] = {
            'used': current,
            'limit': limit,
            'remaining': limit - current,
            'reset_in_seconds': ttl if ttl > 0 else 0
        }

    # Concurrent tasks
    concurrent_key = f"concurrent_tasks:{user_id}"
    current_concurrent = int(redis_client.get(concurrent_key) or 0)

    stats['current_usage']['concurrent_tasks'] = {
        'current': current_concurrent,
        'limit': tier['max_concurrent_tasks'],
        'available': tier['max_concurrent_tasks'] - current_concurrent
    }

    return stats
