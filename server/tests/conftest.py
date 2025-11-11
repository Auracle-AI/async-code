"""
Pytest Configuration and Fixtures
==================================
Shared test configuration and fixtures for integration tests.

Author: Claude Code
Date: 2025-11-11
"""

import pytest
import os
import sys
from flask import Flask

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def app():
    """Create Flask app for testing."""
    from main import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "test-user-123"


@pytest.fixture
def test_github_token():
    """Test GitHub token."""
    return os.getenv('TEST_GITHUB_TOKEN', 'test_token_fake')


@pytest.fixture
def test_repo_url():
    """Test repository URL."""
    return "https://github.com/test/test-repo"


@pytest.fixture
def mock_task_data():
    """Mock task data for testing."""
    return {
        'prompt': 'Create a simple Python function that adds two numbers',
        'repo_url': 'https://github.com/test/test-repo',
        'branch': 'main',
        'github_token': 'test_token',
        'model': 'claude'
    }


@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test (in test environment only)."""
    # Only run in test environment
    if os.getenv('ENVIRONMENT') == 'test':
        # Add database reset logic here
        pass
    yield
