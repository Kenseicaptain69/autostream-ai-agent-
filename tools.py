"""
tools.py — Tool execution layer for AutoStream agent
Uses LangChain @tool decorator for LangGraph integration.
The tool must NOT be triggered until all 3 fields (name, email, platform) are collected.
"""

import json
import os
import logging
from datetime import datetime, timezone
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def mock_lead_capture(name: str, email: str, platform: str) -> str:
    """
    Capture a sales lead with their name, email, and creator platform.
    Call this ONLY when you have collected all three: name, email, and platform.
    In production, this would POST to a CRM like HubSpot or Salesforce.
    """
    # Exact format required by spec (kept as print per spec requirement)
    print(f"Lead captured successfully: {name}, {email}, {platform}")
    logger.info(f"Lead captured successfully: {name}, {email}, {platform}")

    lead = {
        "name": name,
        "email": email,
        "platform": platform,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "status": "new_lead",
        "product": "AutoStream Pro",
    }

    # Persist to leads.json (mock DB)
    try:
        leads_path = os.path.join(os.path.dirname(__file__), "leads.json")
        existing = []
        if os.path.exists(leads_path):
            with open(leads_path, "r") as f:
                existing = json.load(f)
        existing.append(lead)
        with open(leads_path, "w") as f:
            json.dump(existing, f, indent=2)
        logger.info(f"Lead persisted to {leads_path} ({len(existing)} total leads)")
    except Exception as e:
        logger.error(f"Could not persist lead: {e}")

    return json.dumps(lead, indent=2)