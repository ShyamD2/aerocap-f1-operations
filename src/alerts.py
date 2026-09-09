"""
src/alerts.py
Automated Operational Notification & Webhook Dispatcher
Simulates: Microsoft Teams / Slack / Discord webhook alerts for the Brackley Operations Room
"""

import requests
import json
from datetime import datetime


class F1AlertDispatcher:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url

    def dispatch_alert(self, title, message_body, severity="WARNING", metadata=None):
        """
        Formats an operational notification card and dispatches to webhook (or logs to console/file).
        """
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        icons = {
            "CRITICAL": "🚨 [CRITICAL ALERT]",
            "WARNING": "⚠️ [OPERATIONAL WARNING]",
            "INFO": "ℹ️ [SYSTEM NOTICE]",
            "SUCCESS": "✅ [GATE APPROVED]"
        }
        prefix = icons.get(severity, "📢 [F1-OPS]")

        payload = {
            "timestamp": now_str,
            "severity": severity,
            "title": f"{prefix} {title}",
            "body": message_body,
            "metadata": metadata or {}
        }

        # If live webhook is provided, attempt HTTP POST
        if self.webhook_url:
            try:
                requests.post(
                    self.webhook_url,
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=3
                )
            except Exception as e:
                print(f"[Webhook Error] Failed to reach endpoint: {e}")

        # Always return formatted card dictionary for UI/Logging
        return payload
