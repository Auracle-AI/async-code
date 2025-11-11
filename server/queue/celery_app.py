"""
Celery Application for Async Code
==================================
Main Celery app instance and configuration.

Author: Claude Code
Date: 2025-11-11
"""

from celery import Celery
import os

# Create Celery app
app = Celery('async_code')

# Load configuration
app.config_from_object('queue.celeryconfig')

# Auto-discover tasks
app.autodiscover_tasks(['queue'])

if __name__ == '__main__':
    app.start()
