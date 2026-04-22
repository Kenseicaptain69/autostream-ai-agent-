"""
tests/test_tools.py — Pytest suite for tool execution and email validation.
"""

import json
import os
import tempfile
import pytest


# ─── Email Validation (Fix #4) ──────────────────────────────────────────────

class TestEmailValidation:
    """Test stricter email validation from agent._is_valid_email."""

    @pytest.fixture
    def is_valid_email(self):
        from agent import _is_valid_email
        return _is_valid_email

    @pytest.fixture
    def extract_email(self):
        from agent import _extract_email
        return _extract_email

    @pytest.mark.parametrize("email", [
        "john@example.com",
        "jane.doe@company.co.uk",
        "user+tag@gmail.com",
        "test123@domain.org",
        "shreemobarkar@gmail.com",
    ])
    def test_valid_emails(self, is_valid_email, email):
        assert is_valid_email(email) is True

    @pytest.mark.parametrize("email", [
        "a@b.c",           # Too short — local=1 char, domain=3 chars
        "a@b.cc",          # Local part too short (1 char)
        "x@y.co",          # Local part too short (1 char)
        "@domain.com",     # No local part
        "user@",           # No domain
        "notanemail",      # No @ at all
    ])
    def test_invalid_emails(self, is_valid_email, email):
        assert is_valid_email(email) is False

    def test_extract_email_from_text(self, extract_email):
        assert extract_email("my email is john@example.com thanks") == "john@example.com"

    def test_extract_email_returns_none_for_invalid(self, extract_email):
        assert extract_email("my email is a@b.c") is None

    def test_extract_email_no_email(self, extract_email):
        assert extract_email("just some text") is None


# ─── Lead Capture Tool ──────────────────────────────────────────────────────

class TestMockLeadCapture:
    """Test that mock_lead_capture writes correctly to leads.json."""

    def test_lead_capture_returns_json(self):
        from tools import mock_lead_capture
        result = mock_lead_capture.invoke({
            "name": "Test User",
            "email": "test@example.com",
            "platform": "YouTube",
        })
        data = json.loads(result)
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
        assert data["platform"] == "YouTube"
        assert data["status"] == "new_lead"
        assert data["product"] == "AutoStream Pro"
        assert "captured_at" in data

    def test_lead_capture_persists_to_file(self):
        """Verify the lead is appended to leads.json."""
        from tools import mock_lead_capture
        leads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "leads.json")

        # Read current count
        before = []
        if os.path.exists(leads_path):
            with open(leads_path, "r") as f:
                before = json.load(f)

        mock_lead_capture.invoke({
            "name": "Persist Test",
            "email": "persist@test.com",
            "platform": "Twitch",
        })

        with open(leads_path, "r") as f:
            after = json.load(f)

        assert len(after) == len(before) + 1
        assert after[-1]["name"] == "Persist Test"

        # Clean up test data
        with open(leads_path, "w") as f:
            json.dump(before, f, indent=2)
