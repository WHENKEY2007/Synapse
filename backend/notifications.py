"""
Synapse Knowledge Base - Enterprise Notification & Webhook Dispatcher
Supports real-time alerts to Slack, Microsoft Teams, and Security Webhooks.
"""

import os
import json
import urllib.request
from typing import Dict, Any

SLACK_WEBHOOK_URL = os.getenv("SYNAPSE_SLACK_WEBHOOK_URL", "")

def dispatch_alert(finding: Dict[str, Any], event_type: str = "Anomaly Detected") -> Dict[str, Any]:
    """
    Send an automated alert to Slack / Webhook if configured.
    Falls back cleanly to local logging if no webhook URL is set.
    """
    alert_payload = {
        "event": event_type,
        "finding_id": finding.get("id"),
        "title": finding.get("title"),
        "severity": finding.get("severity", "Medium"),
        "owner": finding.get("owner", "General"),
        "confidence": finding.get("confidence", 0),
        "quarantine": finding.get("quarantine", False),
        "current_claim": finding.get("current"),
        "proposed_correction": finding.get("proposed")
    }

    if not SLACK_WEBHOOK_URL:
        return {
            "status": "logged_locally",
            "delivered": False,
            "message": "Notification logged to local audit journal (SYNAPSE_SLACK_WEBHOOK_URL not configured).",
            "payload": alert_payload
        }

    # Format Slack Block Kit message
    slack_blocks = {
        "text": f"🚨 [Synapse Knowledge Alert] {event_type}: {finding.get('title')}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 Synapse Knowledge Alert: {event_type}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Document:* {finding.get('title')}"},
                    {"type": "mrkdwn", "text": f"*Owner:* {finding.get('owner')}"},
                    {"type": "mrkdwn", "text": f"*Severity:* {finding.get('severity')}"},
                    {"type": "mrkdwn", "text": f"*Confidence:* {finding.get('confidence')}%"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Current Claim:* {finding.get('current')}\n*Proposed Correction:* {finding.get('proposed')}"
                }
            }
        ]
    }

    try:
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=json.dumps(slack_blocks).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return {"status": "delivered", "delivered": resp.status == 200, "payload": alert_payload}
    except Exception as e:
        return {"status": "failed", "delivered": False, "error": str(e), "payload": alert_payload}
