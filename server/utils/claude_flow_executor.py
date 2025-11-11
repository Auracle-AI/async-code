"""
Claude-Flow Task Executor
==========================
Executes tasks using claude-flow swarm orchestration.
Replaces the traditional Docker-based execution with swarm intelligence.

Author: Claude Code
Date: 2025-11-11
"""

import logging
import os
import tempfile
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

from database import DatabaseOperations
from utils.claude_flow_adapter import ClaudeFlowAdapter, SwarmTopology

logger = logging.getLogger(__name__)


def run_claude_flow_task(task_id: int, user_id: str, github_token: str) -> None:
    """
    Execute a task using claude-flow swarm orchestration.

    This function is designed to be compatible with the existing
    run_ai_code_task_v2 interface while leveraging claude-flow.

    Args:
        task_id: Task ID in database
        user_id: User ID from Supabase auth
        github_token: GitHub personal access token
    """
    logger.info(f"🐝 Starting claude-flow execution for task {task_id}")

    try:
        # Update task status to running
        DatabaseOperations.update_task(task_id, user_id, {
            'status': 'running',
            'started_at': 'NOW()'
        })

        # Fetch task from database
        task = DatabaseOperations.get_task_by_id(task_id, user_id)
        if not task:
            logger.error(f"❌ Task {task_id} not found")
            return

        # Extract prompt from chat messages
        prompt = _extract_prompt_from_task(task)
        if not prompt:
            logger.error(f"❌ No prompt found for task {task_id}")
            DatabaseOperations.update_task(task_id, user_id, {
                'status': 'failed',
                'error': 'No prompt found in task',
                'completed_at': 'NOW()'
            })
            return

        repo_url = task['repo_url']
        target_branch = task.get('target_branch', 'main')

        # Create temporary directory for git operations
        with tempfile.TemporaryDirectory(prefix=f"claude_flow_task_{task_id}_") as temp_dir:
            temp_path = Path(temp_dir)

            logger.info(f"📂 Created temp directory: {temp_path}")

            # Clone repository
            clone_result = _clone_repository(
                repo_url=repo_url,
                target_dir=temp_path,
                branch=target_branch,
                github_token=github_token
            )

            if not clone_result['success']:
                logger.error(f"❌ Failed to clone repository: {clone_result['error']}")
                DatabaseOperations.update_task(task_id, user_id, {
                    'status': 'failed',
                    'error': f"Repository clone failed: {clone_result['error']}",
                    'completed_at': 'NOW()'
                })
                return

            repo_path = clone_result['repo_path']
            logger.info(f"✅ Repository cloned to: {repo_path}")

            # Initialize claude-flow adapter
            adapter = ClaudeFlowAdapter()

            # Check if bridge is healthy
            if not adapter.health_check():
                logger.error("❌ Claude-flow bridge is not available")
                DatabaseOperations.update_task(task_id, user_id, {
                    'status': 'failed',
                    'error': 'Claude-flow bridge service is not available. Please start it: cd claude-flow-bridge && npm start',
                    'completed_at': 'NOW()'
                })
                return

            # Ensure claude-flow is installed
            if not adapter.check_claude_flow_installed():
                logger.info("📦 Initializing claude-flow...")
                if not adapter.initialize_claude_flow():
                    DatabaseOperations.update_task(task_id, user_id, {
                        'status': 'failed',
                        'error': 'Failed to initialize claude-flow',
                        'completed_at': 'NOW()'
                    })
                    return

            # Store task context in memory for future reference
            adapter.store_memory(
                key=f"task_{task_id}_context",
                content=f"Repository: {repo_url}\nBranch: {target_branch}\nPrompt: {prompt}",
                namespace="async_code_tasks"
            )

            # Execute swarm task
            logger.info(f"🚀 Executing swarm orchestration for task {task_id}")

            result = adapter.execute_swarm_task(
                prompt=prompt,
                repo_path=str(repo_path),
                max_agents=5,
                topology=SwarmTopology.MESH,
                timeout=300  # 5 minutes
            )

            if not result.success:
                logger.error(f"❌ Swarm execution failed: {result.errors}")
                DatabaseOperations.update_task(task_id, user_id, {
                    'status': 'failed',
                    'error': result.errors or 'Swarm execution failed',
                    'execution_metadata': {
                        'execution_time': result.execution_time,
                        'output': result.output[:1000] if result.output else None
                    },
                    'completed_at': 'NOW()'
                })
                return

            logger.info(f"✅ Swarm execution completed in {result.execution_time:.2f}s")
            logger.info(f"🤖 Used {result.agents_used} agents")

            # Get git changes
            git_changes = _get_git_changes(repo_path)

            if not git_changes['has_changes']:
                logger.warning("⚠️ No git changes detected")
                DatabaseOperations.update_task(task_id, user_id, {
                    'status': 'completed',
                    'execution_metadata': {
                        'execution_time': result.execution_time,
                        'agents_used': result.agents_used,
                        'output': result.output[:1000] if result.output else None,
                        'orchestrator': 'claude-flow'
                    },
                    'completed_at': 'NOW()'
                })
                return

            # Update task with results
            update_data = {
                'status': 'completed',
                'git_diff': git_changes['diff'],
                'git_patch': git_changes['patch'],
                'changed_files': git_changes['changed_files'],
                'execution_metadata': {
                    'execution_time': result.execution_time,
                    'agents_used': result.agents_used,
                    'output': result.output[:1000] if result.output else None,
                    'orchestrator': 'claude-flow',
                    'topology': 'mesh'
                },
                'completed_at': 'NOW()'
            }

            DatabaseOperations.update_task(task_id, user_id, update_data)

            logger.info(f"🎉 Task {task_id} completed successfully via claude-flow")
            logger.info(f"📝 Changed files: {len(git_changes['changed_files'])}")

    except Exception as e:
        logger.error(f"💥 Error executing claude-flow task {task_id}: {str(e)}", exc_info=True)
        try:
            DatabaseOperations.update_task(task_id, user_id, {
                'status': 'failed',
                'error': str(e),
                'completed_at': 'NOW()'
            })
        except Exception as update_error:
            logger.error(f"Failed to update task status: {update_error}")


def _extract_prompt_from_task(task: Dict[str, Any]) -> Optional[str]:
    """Extract prompt from task chat messages."""
    chat_messages = task.get('chat_messages', [])
    if not chat_messages:
        return None

    # Find the first user message
    for message in chat_messages:
        if message.get('role') == 'user':
            return message.get('content', '').strip()

    return None


def _clone_repository(
    repo_url: str,
    target_dir: Path,
    branch: str,
    github_token: str
) -> Dict[str, Any]:
    """
    Clone a GitHub repository.

    Args:
        repo_url: Repository URL
        target_dir: Target directory for clone
        branch: Branch to checkout
        github_token: GitHub token for authentication

    Returns:
        Dictionary with success status and repo_path or error
    """
    try:
        # Add token to URL for authentication
        if github_token:
            # Format: https://TOKEN@github.com/owner/repo.git
            auth_url = repo_url.replace('https://github.com/', f'https://{github_token}@github.com/')
        else:
            auth_url = repo_url

        repo_path = target_dir / 'repo'

        # Clone repository
        clone_cmd = [
            'git', 'clone',
            '--depth', '1',
            '--branch', branch,
            '--single-branch',
            auth_url,
            str(repo_path)
        ]

        logger.info(f"🔽 Cloning {repo_url} (branch: {branch})")

        result = subprocess.run(
            clone_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr or 'Clone failed'
            }

        # Configure git
        subprocess.run(
            ['git', 'config', 'user.email', 'claude-flow@async-code.ai'],
            cwd=repo_path,
            capture_output=True
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Claude Flow Bot'],
            cwd=repo_path,
            capture_output=True
        )

        return {
            'success': True,
            'repo_path': repo_path
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def _get_git_changes(repo_path: Path) -> Dict[str, Any]:
    """
    Get git changes from repository.

    Args:
        repo_path: Path to git repository

    Returns:
        Dictionary with diff, patch, and changed files
    """
    try:
        # Get git diff
        diff_result = subprocess.run(
            ['git', 'diff', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=30
        )

        # Get git patch (includes new files)
        patch_result = subprocess.run(
            ['git', 'diff', 'HEAD', '--no-prefix'],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=30
        )

        # Get list of changed files
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=30
        )

        changed_files = []
        for line in status_result.stdout.strip().split('\n'):
            if line.strip():
                # Format: "XY filename"
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    changed_files.append(parts[1])

        has_changes = bool(diff_result.stdout or status_result.stdout)

        return {
            'diff': diff_result.stdout,
            'patch': patch_result.stdout,
            'changed_files': changed_files,
            'has_changes': has_changes
        }

    except Exception as e:
        logger.error(f"Error getting git changes: {e}")
        return {
            'diff': '',
            'patch': '',
            'changed_files': [],
            'has_changes': False,
            'error': str(e)
        }
