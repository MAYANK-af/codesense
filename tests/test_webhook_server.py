import sys
import os
import unittest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add agent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent")))

from webhook_server import app

class TestWebhookServer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["agent"], "CodeSense Webhook Server")

    def test_handle_webhook_unsupported_event(self):
        headers = {"X-GitHub-Event": "push"}
        response = self.client.post("/webhook", headers=headers, json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "skipped")
        self.assertIn("Unsupported event", response.json()["message"])

    def test_handle_webhook_unsupported_action(self):
        headers = {"X-GitHub-Event": "pull_request"}
        payload = {
            "action": "closed",
            "number": 1,
            "repository": {"full_name": "owner/repo"}
        }
        response = self.client.post("/webhook", headers=headers, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "skipped")
        self.assertIn("is not audited", response.json()["message"])

    @patch("webhook_server.run_review_pipeline")
    def test_handle_webhook_success(self, mock_pipeline):
        headers = {"X-GitHub-Event": "pull_request"}
        payload = {
            "action": "opened",
            "number": 42,
            "repository": {"full_name": "owner/repo"}
        }
        response = self.client.post("/webhook", headers=headers, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "queued")
        mock_pipeline.assert_called_once_with("owner/repo", 42)

    @patch("webhook_server.WEBHOOK_SECRET", "my_secret")
    def test_handle_webhook_missing_signature(self):
        headers = {"X-GitHub-Event": "pull_request"}
        response = self.client.post("/webhook", headers=headers, json={})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Missing signature header")

    @patch("webhook_server.WEBHOOK_SECRET", "my_secret")
    def test_handle_webhook_invalid_signature(self):
        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalidsignature"
        }
        response = self.client.post("/webhook", headers=headers, json={})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid signature")

    @patch("webhook_server.WEBHOOK_SECRET", "my_secret")
    @patch("webhook_server.run_review_pipeline")
    def test_handle_webhook_valid_signature(self, mock_pipeline):
        payload = {
            "action": "opened",
            "number": 42,
            "repository": {"full_name": "owner/repo"}
        }
        body = json.dumps(payload).encode()
        mac = hmac.new(b"my_secret", msg=body, digestmod=hashlib.sha256)
        signature = "sha256=" + mac.hexdigest()

        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": signature
        }
        response = self.client.post("/webhook", headers=headers, content=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "queued")
        mock_pipeline.assert_called_once_with("owner/repo", 42)

if __name__ == "__main__":
    unittest.main()
