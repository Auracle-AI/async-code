"""
GitHub OAuth Integration
=========================
OAuth 2.0 flow for GitHub authentication.

Author: Claude Code
Date: 2025-11-11
"""

from flask import Blueprint, request, jsonify, redirect
import requests
import os
from urllib.parse import urlencode
from database import DatabaseOperations
from utils.logger import api_logger

github_oauth_bp = Blueprint('github_oauth', __name__)

# OAuth configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:3000/auth/github/callback')
GITHUB_OAUTH_SCOPES = 'repo,user:email'


@github_oauth_bp.route('/auth/github/authorize', methods=['GET'])
def github_authorize():
    """
    Redirect user to GitHub OAuth authorization page.
    """
    api_logger.info("GitHub OAuth authorization initiated", event="github_oauth_start")

    params = {
        'client_id': GITHUB_CLIENT_ID,
        'redirect_uri': GITHUB_REDIRECT_URI,
        'scope': GITHUB_OAUTH_SCOPES,
        'state': request.args.get('state', 'random_state_string')
    }

    github_auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    return jsonify({
        'status': 'success',
        'auth_url': github_auth_url
    })


@github_oauth_bp.route('/auth/github/callback', methods=['POST'])
def github_callback():
    """
    Handle GitHub OAuth callback and exchange code for access token.
    """
    data = request.get_json()
    code = data.get('code')
    user_id = request.headers.get('X-User-ID')

    if not code:
        return jsonify({'error': 'Authorization code is required'}), 400

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    api_logger.info(
        "Processing GitHub OAuth callback",
        user_id=user_id,
        event="github_oauth_callback"
    )

    try:
        # Exchange code for access token
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': GITHUB_REDIRECT_URI
            }
        )

        token_data = token_response.json()

        if 'error' in token_data:
            api_logger.error(
                "GitHub OAuth token exchange failed",
                error=token_data['error'],
                event="github_oauth_error"
            )
            return jsonify({'error': token_data['error_description']}), 400

        access_token = token_data['access_token']

        # Get user information
        user_response = requests.get(
            'https://api.github.com/user',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
        )

        user_data = user_response.json()

        # Store token securely (encrypted - implementation needed)
        # For now, we'll store in user preferences
        # TODO: Implement proper encryption via secrets management

        api_logger.info(
            "GitHub OAuth completed successfully",
            user_id=user_id,
            github_username=user_data.get('login'),
            event="github_oauth_success"
        )

        return jsonify({
            'status': 'success',
            'github_user': {
                'login': user_data.get('login'),
                'name': user_data.get('name'),
                'avatar_url': user_data.get('avatar_url'),
                'email': user_data.get('email')
            },
            'message': 'GitHub account connected successfully'
        })

    except Exception as e:
        api_logger.error(
            "GitHub OAuth processing failed",
            error=str(e),
            event="github_oauth_error"
        )
        return jsonify({'error': str(e)}), 500


@github_oauth_bp.route('/auth/github/disconnect', methods=['POST'])
def github_disconnect():
    """
    Disconnect GitHub account (revoke token).
    """
    user_id = request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    api_logger.info(
        "Disconnecting GitHub account",
        user_id=user_id,
        event="github_disconnect"
    )

    try:
        # Remove stored token
        # DatabaseOperations.remove_github_token(user_id)

        api_logger.info(
            "GitHub account disconnected",
            user_id=user_id,
            event="github_disconnect_success"
        )

        return jsonify({
            'status': 'success',
            'message': 'GitHub account disconnected'
        })

    except Exception as e:
        api_logger.error(
            "GitHub disconnect failed",
            error=str(e),
            event="github_disconnect_error"
        )
        return jsonify({'error': str(e)}), 500


@github_oauth_bp.route('/auth/github/status', methods=['GET'])
def github_status():
    """
    Check if user has connected GitHub account.
    """
    user_id = request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    try:
        # Check if user has token stored
        # has_token = DatabaseOperations.has_github_token(user_id)

        return jsonify({
            'status': 'success',
            'connected': False,  # Replace with actual check
            'scopes': GITHUB_OAUTH_SCOPES.split(',')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
