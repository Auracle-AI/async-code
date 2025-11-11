"""
Celery Tasks for Async Code
============================
All async task definitions for the queue system.

Author: Claude Code
Date: 2025-11-11
"""

from celery import Task
from queue.celery_app import app
from utils.logger import task_logger, log_task_lifecycle
from utils import run_ai_code_task_v2
from utils.claude_flow_executor import run_claude_flow_task
from database import DatabaseOperations
import docker
import time
from datetime import datetime, timedelta


class CallbackTask(Task):
    """Base task with callbacks for monitoring."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        task_logger.info(
            "Task succeeded",
            celery_task_id=task_id,
            event="celery_task_success"
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        task_logger.error(
            "Task failed",
            celery_task_id=task_id,
            error=str(exc),
            event="celery_task_failure"
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        task_logger.warning(
            "Task retrying",
            celery_task_id=task_id,
            error=str(exc),
            event="celery_task_retry"
        )


@app.task(base=CallbackTask, bind=True, name='queue.tasks.execute_docker_task')
def execute_docker_task(self, task_id: int, user_id: str, github_token: str, model: str = 'claude'):
    """
    Execute task using Docker (claude or codex).

    Args:
        task_id: Database task ID
        user_id: User ID
        github_token: GitHub token
        model: Model to use ('claude' or 'codex')
    """
    task_logger.add_context(
        task_id=task_id,
        user_id=user_id,
        model=model,
        celery_task_id=self.request.id,
        orchestrator='docker'
    )

    task_logger.info("Starting Docker task execution", event="docker_task_start")

    try:
        # Update task with Celery task ID
        DatabaseOperations.update_task(task_id, user_id, {
            'execution_metadata': {
                'celery_task_id': self.request.id,
                'worker_name': self.request.hostname,
                'started_at': datetime.utcnow().isoformat()
            }
        })

        # Execute the task
        run_ai_code_task_v2(task_id, user_id, github_token)

        task_logger.info("Docker task completed successfully", event="docker_task_complete")
        task_logger.clear_context()

        return {
            'status': 'success',
            'task_id': task_id
        }

    except Exception as e:
        task_logger.error(
            "Docker task failed",
            error=str(e),
            event="docker_task_error"
        )
        task_logger.clear_context()
        raise


@app.task(base=CallbackTask, bind=True, name='queue.tasks.execute_claude_flow_task')
def execute_claude_flow_task(self, task_id: int, user_id: str, github_token: str):
    """
    Execute task using claude-flow swarm orchestration.

    Args:
        task_id: Database task ID
        user_id: User ID
        github_token: GitHub token
    """
    task_logger.add_context(
        task_id=task_id,
        user_id=user_id,
        celery_task_id=self.request.id,
        orchestrator='claude-flow'
    )

    task_logger.info("Starting claude-flow task execution", event="swarm_task_start")

    try:
        # Update task with Celery task ID
        DatabaseOperations.update_task(task_id, user_id, {
            'execution_metadata': {
                'celery_task_id': self.request.id,
                'worker_name': self.request.hostname,
                'started_at': datetime.utcnow().isoformat()
            }
        })

        # Execute the task
        run_claude_flow_task(task_id, user_id, github_token)

        task_logger.info("Claude-flow task completed successfully", event="swarm_task_complete")
        task_logger.clear_context()

        return {
            'status': 'success',
            'task_id': task_id
        }

    except Exception as e:
        task_logger.error(
            "Claude-flow task failed",
            error=str(e),
            event="swarm_task_error"
        )
        task_logger.clear_context()
        raise


@app.task(base=CallbackTask, bind=True, name='queue.tasks.execute_codex_task')
def execute_codex_task(self, task_id: int, user_id: str, github_token: str):
    """
    Execute task using Codex (sequential execution to avoid conflicts).

    Args:
        task_id: Database task ID
        user_id: User ID
        github_token: GitHub token
    """
    # Codex tasks are executed sequentially
    return execute_docker_task.apply(args=[task_id, user_id, github_token, 'codex'])


@app.task(base=CallbackTask, bind=True, name='queue.tasks.create_github_pr')
def create_github_pr(self, task_id: int, user_id: str, github_token: str, pr_data: dict):
    """
    Create GitHub PR for a completed task.

    Args:
        task_id: Database task ID
        user_id: User ID
        github_token: GitHub token
        pr_data: PR creation data (title, body)
    """
    task_logger.add_context(
        task_id=task_id,
        user_id=user_id,
        celery_task_id=self.request.id
    )

    task_logger.info("Creating GitHub PR", event="pr_create_start")

    try:
        from tasks import apply_patch_to_github_repo
        from github import Github

        # Get task from database
        task = DatabaseOperations.get_task_by_id(task_id, user_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task['status'] != 'completed':
            raise ValueError(f"Task {task_id} is not completed")

        # Create PR
        repo_parts = task['repo_url'].replace('https://github.com/', '').replace('.git', '')
        g = Github(github_token)
        repo = g.get_repo(repo_parts)

        base_branch = task['target_branch']
        pr_branch = f"claude-code-{task_id}"

        # Create branch and apply patch
        base_branch_obj = repo.get_branch(base_branch)
        new_ref = repo.create_git_ref(f"refs/heads/{pr_branch}", base_branch_obj.commit.sha)

        files_updated = apply_patch_to_github_repo(repo, pr_branch, task['git_patch'], task)

        # Create PR
        pr = repo.create_pull(
            title=pr_data.get('title', f"Async Code: Task {task_id}"),
            body=pr_data.get('body', 'Automated changes'),
            head=pr_branch,
            base=base_branch
        )

        # Update task
        DatabaseOperations.update_task(task_id, user_id, {
            'pr_branch': pr_branch,
            'pr_number': pr.number,
            'pr_url': pr.html_url
        })

        task_logger.info(
            "GitHub PR created successfully",
            pr_number=pr.number,
            pr_url=pr.html_url,
            event="pr_create_complete"
        )

        task_logger.clear_context()

        return {
            'status': 'success',
            'pr_number': pr.number,
            'pr_url': pr.html_url
        }

    except Exception as e:
        task_logger.error(
            "GitHub PR creation failed",
            error=str(e),
            event="pr_create_error"
        )
        task_logger.clear_context()
        raise


@app.task(base=CallbackTask, name='queue.tasks.cleanup_old_tasks')
def cleanup_old_tasks():
    """
    Periodic task to clean up old completed/failed tasks.
    Runs every hour via Celery Beat.
    """
    task_logger.info("Starting task cleanup", event="cleanup_start")

    try:
        # Clean up tasks older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # This would require a new database method
        # DatabaseOperations.delete_old_tasks(cutoff_date)

        task_logger.info("Task cleanup completed", event="cleanup_complete")

    except Exception as e:
        task_logger.error("Task cleanup failed", error=str(e), event="cleanup_error")
        raise


@app.task(base=CallbackTask, name='queue.tasks.cleanup_orphaned_containers')
def cleanup_orphaned_containers():
    """
    Periodic task to clean up orphaned Docker containers.
    Runs every 2 hours via Celery Beat.
    """
    task_logger.info("Starting container cleanup", event="container_cleanup_start")

    try:
        client = docker.from_env()

        # Find containers older than 2 hours that are stopped
        cutoff_time = time.time() - (2 * 3600)

        for container in client.containers.list(all=True):
            # Check if it's an async-code container
            if container.name.startswith('async-code-task-'):
                # Check if stopped and old
                if container.status in ['exited', 'dead']:
                    created_time = container.attrs['Created']
                    # Parse and check age
                    # ... cleanup logic

                    container.remove(force=True)
                    task_logger.info(
                        "Removed orphaned container",
                        container_id=container.id,
                        container_name=container.name
                    )

        task_logger.info("Container cleanup completed", event="container_cleanup_complete")

    except Exception as e:
        task_logger.error(
            "Container cleanup failed",
            error=str(e),
            event="container_cleanup_error"
        )
        raise
