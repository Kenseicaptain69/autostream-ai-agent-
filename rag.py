"""
rag.py — Retrieval-Augmented Generation for AutoStream knowledge base
"""

import json
import os
import logging

logger = logging.getLogger(__name__)


def load_knowledge_base() -> dict:
    """Load knowledge.json from the same directory."""
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge.json")
    try:
        with open(kb_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Knowledge base not found at {kb_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in knowledge base: {e}")
        return {}


def retrieve_context(query: str) -> str:
    """
    Simple keyword-based retrieval from knowledge base.
    Returns a formatted string to inject into the LLM prompt.
    """
    kb = load_knowledge_base()
    if not kb:
        return "Knowledge base unavailable."

    query_lower = query.lower()
    sections = []

    # Pricing / plan triggers
    if any(kw in query_lower for kw in ["price", "pricing", "cost", "plan", "basic", "pro", "how much", "cheap", "expensive"]):
        sections.append("=== PRICING PLANS ===")
        sections.append(f"Basic Plan: {kb['basic_plan']['price']} | {kb['basic_plan']['videos']} | {kb['basic_plan']['resolution']} | Features: {', '.join(kb['basic_plan']['features'])}")
        sections.append(f"Pro Plan: {kb['pro_plan']['price']} | {kb['pro_plan']['videos']} | {kb['pro_plan']['resolution']} | Features: {', '.join(kb['pro_plan']['features'])}")

    # Policy triggers
    if any(kw in query_lower for kw in ["refund", "cancel", "support", "help", "policy", "trial"]):
        sections.append("=== POLICIES ===")
        sections.append(f"Refund Policy: {kb['policies']['refund']}")
        sections.append(f"Support: {kb['policies']['support']}")
        sections.append(f"Trial: {kb['policies']['trial']}")

    # Platform / product triggers
    if any(kw in query_lower for kw in ["platform", "youtube", "twitch", "instagram", "tiktok", "what is", "autostream", "feature"]):
        sections.append("=== PRODUCT INFO ===")
        sections.append(f"Product: {kb['general']['product']} — {kb['general']['description']}")
        sections.append(f"Supported Platforms: {', '.join(kb['general']['platforms'])}")

    # Default: return full knowledge if no specific match
    if not sections:
        sections.append("=== AUTOSTREAM KNOWLEDGE BASE ===")
        sections.append(f"Basic Plan: {kb['basic_plan']['price']} | {kb['basic_plan']['videos']} | {kb['basic_plan']['resolution']}")
        sections.append(f"Pro Plan: {kb['pro_plan']['price']} | {kb['pro_plan']['videos']} | {kb['pro_plan']['resolution']} | Features: {', '.join(kb['pro_plan']['features'])}")
        sections.append(f"Refund: {kb['policies']['refund']} | Support: {kb['policies']['support']}")

    logger.debug(f"RAG retrieved {len(sections)} sections for query: '{query[:50]}...'")
    return "\n".join(sections)