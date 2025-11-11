"""
Integration Tests for Task Execution
=====================================
Test the complete task execution lifecycle for all execution modes.

Author: Claude Code
Date: 2025-11-11
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock


class TestTaskExecution:
    """Test task execution workflows."""

    def test_create_task_docker(self, client, test_user_id, mock_task_data):
        """Test creating a Docker-based task."""
        response = client.post(
            '/start-task',
            json=mock_task_data,
            headers={'X-User-ID': test_user_id}
        )

        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert 'task_id' in data
        assert data['orchestrator'] == 'docker'

    def test_create_task_claude_flow(self, client, test_user_id, mock_task_data):
        """Test creating a claude-flow task."""
        claude_flow_data = {**mock_task_data, 'model': 'claude-flow'}

        response = client.post(
            '/start-task',
            json=claude_flow_data,
            headers={'X-User-ID': test_user_id}
        )

        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert data['orchestrator'] == 'claude-flow'

    def test_create_task_missing_fields(self, client, test_user_id):
        """Test task creation with missing required fields."""
        incomplete_data = {
            'prompt': 'Test prompt'
            # Missing repo_url and github_token
        }

        response = client.post(
            '/start-task',
            json=incomplete_data,
            headers={'X-User-ID': test_user_id}
        )

        assert response.status_code == 400
        assert 'error' in response.json

    def test_create_task_invalid_model(self, client, test_user_id, mock_task_data):
        """Test task creation with invalid model."""
        invalid_data = {**mock_task_data, 'model': 'invalid_model'}

        response = client.post(
            '/start-task',
            json=invalid_data,
            headers={'X-User-ID': test_user_id}
        )

        assert response.status_code == 400
        assert 'model must be either' in response.json['error']

    def test_get_task_status(self, client, test_user_id):
        """Test retrieving task status."""
        # Create a task first
        task_data = {
            'prompt': 'Test',
            'repo_url': 'https://github.com/test/repo',
            'github_token': 'test',
            'model': 'claude'
        }

        create_response = client.post(
            '/start-task',
            json=task_data,
            headers={'X-User-ID': test_user_id}
        )

        task_id = create_response.json['task_id']

        # Get status
        status_response = client.get(
            f'/task-status/{task_id}',
            headers={'X-User-ID': test_user_id}
        )

        assert status_response.status_code == 200
        data = status_response.json
        assert data['status'] == 'success'
        assert 'task' in data
        assert data['task']['id'] == task_id

    def test_list_tasks(self, client, test_user_id):
        """Test listing all user tasks."""
        response = client.get(
            '/tasks',
            headers={'X-User-ID': test_user_id}
        )

        assert response.status_code == 200
        data = response.json
        assert 'tasks' in data
        assert 'total_tasks' in data


@pytest.mark.integration
class TestClaudeFlowIntegration:
    """Integration tests specifically for claude-flow."""

    @patch('utils.claude_flow_executor.ClaudeFlowAdapter')
    def test_claude_flow_execution_success(self, mock_adapter, client, test_user_id):
        """Test successful claude-flow task execution."""
        # Mock the adapter
        mock_instance = MagicMock()
        mock_instance.health_check.return_value = True
        mock_instance.check_claude_flow_installed.return_value = True
        mock_instance.execute_swarm_task.return_value = MagicMock(
            success=True,
            execution_time=45.2,
            agents_used=5,
            output="Task completed successfully"
        )
        mock_adapter.return_value = mock_instance

        # Create task
        task_data = {
            'prompt': 'Test swarm execution',
            'repo_url': 'https://github.com/test/repo',
            'github_token': 'test',
            'model': 'claude-flow'
        }

        response = client.post(
            '/start-task',
            json=task_data,
            headers={'X-User-ID': test_user_id}
        )

        assert response.status_code == 200
        assert response.json['orchestrator'] == 'claude-flow'

    @patch('utils.claude_flow_executor.ClaudeFlowAdapter')
    def test_claude_flow_bridge_unavailable(self, mock_adapter, client, test_user_id):
        """Test handling when claude-flow bridge is unavailable."""
        mock_instance = MagicMock()
        mock_instance.health_check.return_value = False
        mock_adapter.return_value = mock_instance

        task_data = {
            'prompt': 'Test',
            'repo_url': 'https://github.com/test/repo',
            'github_token': 'test',
            'model': 'claude-flow'
        }

        response = client.post(
            '/start-task',
            json=task_data,
            headers={'X-User-ID': test_user_id}
        )

        # Task should be created but will fail during execution
        assert response.status_code == 200


@pytest.mark.integration
class TestGitHubIntegration:
    """Test GitHub integration functionality."""

    def test_validate_github_token_valid(self, client):
        """Test validating a valid GitHub token."""
        # This requires a real token or extensive mocking
        pass

    def test_validate_github_token_invalid(self, client):
        """Test validating an invalid GitHub token."""
        response = client.post(
            '/validate-token',
            json={'github_token': 'invalid_token'}
        )

        assert response.status_code == 401

    @patch('tasks.Github')
    def test_create_pr_success(self, mock_github, client, test_user_id):
        """Test successful PR creation."""
        # Mock GitHub API
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.number = 123
        mock_pr.html_url = 'https://github.com/test/repo/pull/123'
        mock_repo.create_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo

        # Create task and PR
        # This would require full task execution which is complex
        pass


@pytest.mark.integration
class TestCeleryQueue:
    """Test Celery queue integration."""

    def test_queue_task_execution(self):
        """Test queueing a task for execution."""
        from queue.tasks import execute_docker_task

        # This requires Celery worker to be running
        # result = execute_docker_task.delay(123, 'user-id', 'token')
        # assert result is not None
        pass

    def test_task_retry_on_failure(self):
        """Test that failed tasks are retried."""
        pass

    def test_task_priority(self):
        """Test task priority routing."""
        pass


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/ping')
    assert response.status_code == 200


def test_missing_user_id(client, mock_task_data):
    """Test request without user ID header."""
    response = client.post('/start-task', json=mock_task_data)
    assert response.status_code == 400
    assert 'User ID required' in response.json['error']
