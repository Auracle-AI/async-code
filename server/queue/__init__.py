"""
Async Queue Module
==================
Celery-based async task queue for production-grade task execution.
"""

from queue.celery_app import app as celery_app
from queue import tasks

__all__ = ['celery_app', 'tasks']
