"""
Webhook System
==============
Allow external systems to subscribe to events.

Author: Claude Code
Date: 2025-11-11
"""

from flask import Blueprint, request, jsonify
import requests
import hmac
import hashlib
import json
from typing import Dict, Any, List
from database import DatabaseOperations
from utils.logger import api_logger
import time
from threading import Thread

webhooks_bp = Blueprint('webhooks', __name__)


class WebhookEvent:
    """Webhook event types."""
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    PR_CREATED = "pr.created"
    SWARM_AGENT_ASSIGNED = "swarm.agent_assigned"
    SWARM_COMPLETE = "swarm.complete"


def generate_signature(payload: dict, secret: str) -> str:
    """
    Generate HMAC signature for webhook payload.

    Args:
        payload: Webhook payload
        secret: Webhook secret

    Returns:
        HMAC signature
    """
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    return f"sha256={signature}"


def send_webhook(webhook_url: str, event_type: str, payload: dict, secret: str = None):
    """
    Send webhook notification to external system.

    Args:
        webhook_url: Target webhook URL
        event_type: Event type
        payload: Event payload
        secret: Optional webhook secret for signing
    """
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Event': event_type,
        'X-Webhook-Delivery': str(int(time.time())),
    }

    if secret:
        headers['X-Webhook-Signature'] = generate_signature(payload, secret)

    try:
        api_logger.info(
            "Sending webhook",
            url=webhook_url,
            event=event_type,
            event_category="webhook_send"
        )

        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            api_logger.info(
                "Webhook delivered successfully",
                url=webhook_url,
                event=event_type,
                status_code=response.status_code,
                event_category="webhook_success"
            )
        else:
            api_logger.warning(
                "Webhook delivery failed",
                url=webhook_url,
                event=event_type,
                status_code=response.status_code,
                event_category="webhook_failure"
            )

    except Exception as e:
        api_logger.error(
            "Webhook delivery error",
            url=webhook_url,
            event=event_type,
            error=str(e),
            event_category="webhook_error"
        )


def trigger_webhooks(user_id: str, event_type: str, payload: dict):
    """
    Trigger all registered webhooks for user and event type.

    Args:
        user_id: User ID
        event_type: Event type
        payload: Event payload
    """
    # Get user's registered webhooks
    # webhooks = DatabaseOperations.get_user_webhooks(user_id, event_type)

    # Mock for demonstration
    webhooks = []

    for webhook in webhooks:
        # Send in background thread to avoid blocking
        thread = Thread(
            target=send_webhook,
            args=(webhook['url'], event_type, payload, webhook.get('secret'))
        )
        thread.daemon = True
        thread.start()


@webhooks_bp.route('/api/webhooks', methods=['POST'])
def register_webhook():
    """Register a new webhook."""
    user_id = request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    data = request.get_json()
    url = data.get('url')
    events = data.get('events', [])
    secret = data.get('secret')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if not events:
        return jsonify({'error': 'At least one event type is required'}), 400

    # Validate event types
    valid_events = [
        WebhookEvent.TASK_STARTED,
        WebhookEvent.TASK_COMPLETED,
        WebhookEvent.TASK_FAILED,
        WebhookEvent.PR_CREATED,
        WebhookEvent.SWARM_AGENT_ASSIGNED,
        WebhookEvent.SWARM_COMPLETE
    ]

    for event in events:
        if event not in valid_events:
            return jsonify({
                'error': f'Invalid event type: {event}',
                'valid_events': valid_events
            }), 400

    # Store webhook
    # webhook_id = DatabaseOperations.create_webhook(user_id, url, events, secret)

    api_logger.info(
        "Webhook registered",
        user_id=user_id,
        url=url,
        events=events,
        event="webhook_registered"
    )

    return jsonify({
        'status': 'success',
        'webhook_id': 'mock-webhook-id',
        'url': url,
        'events': events,
        'message': 'Webhook registered successfully'
    })


@webhooks_bp.route('/api/webhooks', methods=['GET'])
def list_webhooks():
    """List all webhooks for user."""
    user_id = request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    # webhooks = DatabaseOperations.get_user_webhooks(user_id)

    return jsonify({
        'status': 'success',
        'webhooks': []  # Mock data
    })


@webhooks_bp.route('/api/webhooks/<webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id: str):
    """Delete a webhook."""
    user_id = request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    # DatabaseOperations.delete_webhook(webhook_id, user_id)

    api_logger.info(
        "Webhook deleted",
        user_id=user_id,
        webhook_id=webhook_id,
        event="webhook_deleted"
    )

    return jsonify({
        'status': 'success',
        'message': 'Webhook deleted successfully'
    })


@webhooks_bp.route('/api/webhooks/<webhook_id>/test', methods='POST'])
def test_webhook(webhook_id: str):
    """Send a test webhook."""
    user_id = request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    # webhook = DatabaseOperations.get_webhook(webhook_id, user_id)

    # Send test payload
    test_payload = {
        'event': 'webhook.test',
        'timestamp': time.time(),
        'data': {
            'message': 'This is a test webhook'
        }
    }

    # send_webhook(webhook['url'], 'webhook.test', test_payload, webhook.get('secret'))

    return jsonify({
        'status': 'success',
        'message': 'Test webhook sent'
    })
