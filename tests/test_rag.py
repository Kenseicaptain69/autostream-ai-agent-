"""
tests/test_rag.py — Pytest suite for RAG knowledge retrieval edge cases.
"""

import pytest
from rag import retrieve_context, load_knowledge_base


class TestLoadKnowledgeBase:
    """Test knowledge base loading."""

    def test_loads_successfully(self):
        kb = load_knowledge_base()
        assert isinstance(kb, dict)
        assert "general" in kb
        assert "basic_plan" in kb
        assert "pro_plan" in kb
        assert "policies" in kb

    def test_data_integrity(self):
        """Verify exact data points from spec."""
        kb = load_knowledge_base()
        assert kb["basic_plan"]["price"] == "$29/month"
        assert kb["basic_plan"]["videos"] == "10/month"
        assert kb["basic_plan"]["resolution"] == "720p"
        assert kb["pro_plan"]["price"] == "$79/month"
        assert kb["pro_plan"]["videos"] == "Unlimited"
        assert kb["pro_plan"]["resolution"] == "4K"
        assert "AI captions" in kb["pro_plan"]["features"]
        assert "No refunds after 7 days" in kb["policies"]["refund"]
        assert "24/7 support only for Pro" in kb["policies"]["support"]


class TestRetrieveContext:
    """Test keyword-based RAG retrieval returns correct sections."""

    @pytest.mark.parametrize("query,expected_section", [
        ("What are your pricing plans?", "PRICING PLANS"),
        ("How much does it cost?", "PRICING PLANS"),
        ("Tell me about the Pro plan", "PRICING PLANS"),
    ])
    def test_pricing_queries(self, query, expected_section):
        context = retrieve_context(query)
        assert expected_section in context

    @pytest.mark.parametrize("query,expected_section", [
        ("What is your refund policy?", "POLICIES"),
        ("Do you have 24/7 support?", "POLICIES"),
        ("Is there a free trial?", "POLICIES"),
    ])
    def test_policy_queries(self, query, expected_section):
        context = retrieve_context(query)
        assert expected_section in context

    @pytest.mark.parametrize("query,expected_section", [
        ("What platforms do you support?", "PRODUCT INFO"),
        ("Tell me about AutoStream", "PRODUCT INFO"),
        ("Do you support YouTube?", "PRODUCT INFO"),
        ("What features do you offer?", "PRODUCT INFO"),
    ])
    def test_product_queries(self, query, expected_section):
        context = retrieve_context(query)
        assert expected_section in context

    def test_default_fallback(self):
        """Unrecognized queries should return full knowledge base."""
        context = retrieve_context("something completely random xyz")
        assert "AUTOSTREAM KNOWLEDGE BASE" in context
        assert "$29/month" in context
        assert "$79/month" in context

    def test_multi_section_query(self):
        """A query matching multiple categories should return all matching sections."""
        context = retrieve_context("What's the price and refund policy?")
        assert "PRICING PLANS" in context
        assert "POLICIES" in context

    def test_returns_actual_data(self):
        """Verify the returned context contains real KB values."""
        context = retrieve_context("pricing")
        assert "$29/month" in context
        assert "$79/month" in context
        assert "4K" in context
