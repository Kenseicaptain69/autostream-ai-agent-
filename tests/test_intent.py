"""
tests/test_intent.py — Pytest suite for intent classification and platform extraction.
Covers edge cases from improvement summary: #3 (name detection), #5 (casing), #7 ("try").
"""

import pytest
from intent import _rule_based_intent, extract_platform, classify_intent


# ─── Intent Classification ───────────────────────────────────────────────────

class TestRuleBasedIntent:
    """Test _rule_based_intent covers all expected keyword categories."""

    @pytest.mark.parametrize("text,expected", [
        ("Hi, tell me about your pricing.", "product_query"),
        ("What are your plans?", "product_query"),
        ("How much does it cost?", "product_query"),
        ("Tell me about the Pro plan features", "product_query"),
        ("What's the refund policy?", "product_query"),
        ("Do you have 4K support?", "product_query"),
    ])
    def test_product_query(self, text, expected):
        assert _rule_based_intent(text) == expected

    @pytest.mark.parametrize("text,expected", [
        ("I want to sign up for Pro", "high_intent"),
        ("I want the Pro plan for my YouTube channel", "high_intent"),
        ("Sign me up!", "high_intent"),
        ("I'd like to subscribe", "high_intent"),
        ("I want to buy the Pro plan", "high_intent"),
        ("I'm interested in AutoStream", "high_intent"),
        ("I want to upgrade", "high_intent"),
        ("I'm in, let's get started", "high_intent"),
    ])
    def test_high_intent(self, text, expected):
        assert _rule_based_intent(text) == expected

    @pytest.mark.parametrize("text,expected", [
        ("hi", "greeting"),
        ("hello", "greeting"),
        ("hey", "greeting"),
        ("Hello there!", "greeting"),
        ("Hi, how are you?", "greeting"),
        ("good morning", "greeting"),
    ])
    def test_greeting(self, text, expected):
        assert _rule_based_intent(text) == expected

    @pytest.mark.parametrize("text,expected", [
        ("john@example.com", "provide_email"),
        ("my.email+tag@company.co.uk", "provide_email"),
    ])
    def test_email_detection(self, text, expected):
        assert _rule_based_intent(text) == expected

    @pytest.mark.parametrize("text", [
        "John Doe",
        "thanks",
        "okay",
        "sure",
    ])
    def test_other(self, text):
        assert _rule_based_intent(text) == "other"

    # ── Fix #7: "try" should NOT trigger high_intent ─────────────────────
    def test_try_not_high_intent(self):
        """'Can I try the free trial?' should be product_query, not high_intent."""
        assert _rule_based_intent("Can I try the free trial?") == "product_query"

    def test_try_in_product_context(self):
        """'try' is now a product keyword."""
        assert _rule_based_intent("Can I try it?") == "product_query"


# ─── Platform Extraction ─────────────────────────────────────────────────────

class TestExtractPlatform:
    """Test platform extraction with correct casing (Fix #5)."""

    @pytest.mark.parametrize("text,expected", [
        ("I stream on YouTube", "YouTube"),
        ("my youtube channel", "YouTube"),
        ("I use TikTok", "TikTok"),
        ("tiktok is great", "TikTok"),
        ("streaming on Twitch", "Twitch"),
        ("I post on Instagram", "Instagram"),
        ("Facebook page", "Facebook"),
        ("LinkedIn content", "LinkedIn"),
        ("Twitter account", "Twitter"),
        ("I'm on X", "X"),
    ])
    def test_correct_casing(self, text, expected):
        """Platform names should use proper brand casing, not .title()."""
        assert extract_platform(text) == expected

    def test_no_platform(self):
        assert extract_platform("I like streaming") == ""

    def test_youtube_not_title_case_bug(self):
        """Regression: .title() would produce 'Youtube' not 'YouTube'."""
        result = extract_platform("youtube")
        assert result == "YouTube"
        assert result != "Youtube"  # The old bug

    def test_tiktok_not_title_case_bug(self):
        """Regression: .title() would produce 'Tiktok' not 'TikTok'."""
        result = extract_platform("tiktok")
        assert result == "TikTok"
        assert result != "Tiktok"


# ─── Name Detection (Fix #3) ────────────────────────────────────────────────

class TestNameDetection:
    """Test that _looks_like_command doesn't reject valid names."""

    # Import from agent
    @pytest.fixture
    def looks_like_command(self):
        from agent import _looks_like_command
        return _looks_like_command

    @pytest.mark.parametrize("name", [
        "John Doe",
        "Jane Smith",
        "Canton",       # Previously matched "can" substring
        "Howie",        # Previously matched "how" substring
        "Hope",
        "Grace",
        "Will Smith",   # "Will" as a name — but "will" isn't in cmd_words; safe
        "Shelby",
        "Ethan",
        "Priya",
        "Shreeyash",
    ])
    def test_valid_names_not_rejected(self, looks_like_command, name):
        """Real names should NOT be flagged as commands."""
        assert looks_like_command(name) is False, f"'{name}' was incorrectly flagged as a command"

    @pytest.mark.parametrize("text", [
        "What is the price?",
        "Tell me about plans",
        "How much does it cost?",
        "Can you help me?",
        "Show me features",
        "Hi there",
        "I want to sign up",
    ])
    def test_commands_detected(self, looks_like_command, text):
        """Commands/questions should be flagged."""
        assert looks_like_command(text) is True, f"'{text}' should be flagged as a command"
