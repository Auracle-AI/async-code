"""
Celery Configuration for Async Code
====================================
Production-grade async task queue configuration.

Author: Claude Code
Date: 2025-11-11
"""

import os
from kombu import Queue, Exchange

# Redis connection
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Broker settings
broker_url = REDIS_URL
result_backend = REDIS_URL

# Task serialization
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task execution
task_track_started = True
task_time_limit = 3600  # 1 hour hard limit
task_soft_time_limit = 3000  # 50 minutes soft limit
task_acks_late = True  # Acknowledge after task completion
worker_prefetch_multiplier = 1  # One task at a time per worker

# Result backend settings
result_expires = 86400  # Results expire after 24 hours

# Task routing
task_routes = {
    'queue.tasks.execute_docker_task': {'queue': 'docker'},
    'queue.tasks.execute_claude_flow_task': {'queue': 'claude_flow'},
    'queue.tasks.execute_codex_task': {'queue': 'codex'},
    'queue.tasks.create_github_pr': {'queue': 'github'},
    'queue.tasks.cleanup_old_tasks': {'queue': 'maintenance'},
}

# Queue definitions
task_queues = (
    Queue('docker', Exchange('tasks'), routing_key='tasks.docker',
          queue_arguments={'x-max-priority': 10}),
    Queue('claude_flow', Exchange('tasks'), routing_key='tasks.claude_flow',
          queue_arguments={'x-max-priority': 10}),
    Queue('codex', Exchange('tasks'), routing_key='tasks.codex',
          queue_arguments={'x-max-priority': 10}),
    Queue('github', Exchange('tasks'), routing_key='tasks.github',
          queue_arguments={'x-max-priority': 5}),
    Queue('maintenance', Exchange('tasks'), routing_key='tasks.maintenance',
          queue_arguments={'x-max-priority': 1}),
)

# Task priority routing
task_default_priority = 5

# Retry policy
task_autoretry_for = (Exception,)
task_retry_kwargs = {'max_retries': 3}
task_retry_backoff = True
task_retry_backoff_max = 600  # 10 minutes max
task_retry_jitter = True

# Beat schedule (periodic tasks)
beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'queue.tasks.cleanup_old_tasks',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-orphaned-containers': {
        'task': 'queue.tasks.cleanup_orphaned_containers',
        'schedule': 7200.0,  # Every 2 hours
    },
}

# Worker settings
worker_max_tasks_per_child = 100  # Recycle worker after 100 tasks
worker_disable_rate_limits = False
worker_send_task_events = True
task_send_sent_event = True

# Monitoring
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
