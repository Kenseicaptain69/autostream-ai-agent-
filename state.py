"""
state.py — LangGraph state schema for AutoStream AI Agent
Uses TypedDict with add_messages reducer for conversation history.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """LangGraph state schema for the AutoStream conversation agent."""
    # Conversation history — add_messages reducer auto-appends new messages
    messages: Annotated[list, add_messages]
    # Current classified intent
    intent: str
    # Lead capture fields (all 3 required before tool executes)
    name: Optional[str]
    email: Optional[str]
    platform: Optional[str]
    # Flow control flags
    in_lead_flow: bool
    lead_captured: bool


def get_missing_lead_field(state: AgentState) -> Optional[str]:
    """Return the next missing field in lead capture sequence: name → email → platform."""
    if not state.get("name"):
        return "name"
    if not state.get("email"):
        return "email"
    if not state.get("platform"):
        return "platform"
    return None


def is_lead_complete(state: AgentState) -> bool:
    """Check if all 3 lead fields are collected."""
    return bool(state.get("name") and state.get("email") and state.get("platform"))