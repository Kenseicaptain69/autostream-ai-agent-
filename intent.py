"""
intent.py — Intent classification for AutoStream agent
Uses rule-based keyword matching for reliable, fast classification.
"""

import re


# Known creator platforms for extraction
PLATFORMS = ["youtube", "twitch", "instagram", "tiktok", "facebook", "linkedin", "twitter", "x"]

# Proper display names for each platform (avoids .title() issues like "Youtube" → "YouTube")
PLATFORM_DISPLAY = {
    "youtube": "YouTube",
    "twitch": "Twitch",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "twitter": "Twitter",
    "x": "X",
}


def classify_intent(user_message: str, conversation_context: str = "") -> str:
    """Classify user intent using rule-based keyword matching."""
    return _rule_based_intent(user_message)


def extract_platform(text: str) -> str:
    """Extract a creator platform name from user text if mentioned.
    Returns the correctly-cased display name (e.g. 'YouTube', 'TikTok')."""
    text_lower = text.lower()
    for p in PLATFORMS:
        if p in text_lower:
            return PLATFORM_DISPLAY[p]
    return ""


def _rule_based_intent(text: str) -> str:
    """Keyword-based intent classification with priority ordering."""
    text = text.lower().strip()

    # 1. High-intent (most specific — check first)
    #    NOTE: "try" removed — it caused "Can I try the free trial?" to be misclassified
    #    as high_intent instead of product_query. Users express purchase intent via
    #    "sign up", "subscribe", "buy", "get started", "interested", etc.
    high_intent_kws = ["want", "sign up", "sign me", "subscribe", "buy", "purchase",
                       "get started", "upgrade", "i'm in", "im in", "interested"]
    if any(kw in text for kw in high_intent_kws):
        return "high_intent"

    # 2. Product or pricing inquiry
    product_kws = ["price", "pricing", "plan", "cost", "feature", "refund", "support",
                   "platform", "4k", "caption", "video", "how much", "compare", "trial", "try"]
    if any(kw in text for kw in product_kws):
        return "product_query"

    # 3. Casual greeting (checked last — broad patterns)
    greetings = ["hi", "hello", "hey", "good morning", "good evening", "howdy"]
    if any(text == g or text.startswith(g + " ") or text.startswith(g + ",") for g in greetings):
        return "greeting"

    # 4. Email detection
    if re.match(r"[^@]+@[^@]+\.[^@]+", text):
        return "provide_email"

    return "other"