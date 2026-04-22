"""
agent.py — Core AutoStream AI Agent using LangGraph StateGraph

Expected Conversation Flow:
  1. User: "Hi, tell me about your pricing."        → greeting + product_query → RAG pricing
  2. User: "I want Pro plan for my YouTube channel." → high_intent → extract platform → ask name
  3. User: "John Doe"                                → provide_name → ask email
  4. User: "john@example.com"                        → provide_email → tool fires → confirmation

Key: Platform is auto-extracted from the high-intent message.
     Agent only explicitly asks for Name and Email.
     Tool fires ONLY after all 3 fields are collected.
"""

import os
import re
import time
import logging
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState, get_missing_lead_field, is_lead_complete
from intent import classify_intent, extract_platform, _rule_based_intent
from rag import retrieve_context
from tools import mock_lead_capture

load_dotenv()

logger = logging.getLogger(__name__)

# ─── LLM Setup ──────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_output_tokens=400,
    max_retries=2,
)

SYSTEM_PROMPT = """You are AutoStream's friendly and professional sales assistant.

AutoStream is a SaaS platform for automated video streaming and content management.

Rules:
- Be concise, warm, and helpful
- When answering product questions, use ONLY the knowledge base context provided
- Do not invent features or prices — only state what is in the knowledge base
- When collecting lead info, ask ONE field at a time (name first, then email)
- Never ask for name/email unless the user has shown buying intent
- Keep responses short (2-3 sentences max)
"""


# ─── LLM Retry Helper ───────────────────────────────────────────────────────

def _invoke_llm_with_retry(messages, max_retries=3):
    """Invoke LLM with exponential backoff on rate limit / quota errors.
    Handles Gemini 429 and quota-exceeded responses gracefully."""
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = any(kw in error_str for kw in ["429", "quota", "rate", "resource_exhausted"])
            if is_rate_limit and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                logger.warning(f"Rate limited (attempt {attempt+1}/{max_retries}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"LLM invocation failed: {e}")
                raise
    raise Exception("LLM rate limit exceeded after retries")


# ─── Email Validation ────────────────────────────────────────────────────────

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

def _is_valid_email(email: str) -> bool:
    """Validate email with stricter rules beyond basic regex.
    Rejects ultra-short emails like a@b.c that pass basic regex."""
    if not EMAIL_REGEX.fullmatch(email):
        return False
    local, domain = email.rsplit("@", 1)
    # Require at least 2-char local part and 4-char domain (e.g. "ab.co")
    if len(local) < 2 or len(domain) < 4:
        return False
    return True

def _extract_email(text: str):
    """Extract and validate an email from text. Returns email string or None."""
    match = EMAIL_REGEX.search(text)
    if match:
        email = match.group()
        if _is_valid_email(email):
            return email
    return None


# ─── Name Detection ─────────────────────────────────────────────────────────

def _looks_like_command(text: str) -> bool:
    """Check if text looks like a command/question rather than a name.
    Uses word-boundary matching to avoid false positives on names like
    'Canton' (previously matched 'can'), 'Howie' (matched 'how'), etc."""
    text_lower = text.lower().strip()
    # Split into words for boundary-aware matching
    words = set(re.split(r'\s+', text_lower))
    cmd_words = {"hi", "hello", "price", "plan", "want", "buy", "cost",
                 "what", "how", "can", "tell", "show", "help"}
    # If any word IS a command word, it's probably not a name
    if words & cmd_words:
        return True
    # Multi-word command phrases (still use substring matching)
    cmd_phrases = ["sign up", "get started", "how much", "tell me", "i want", "what is"]
    return any(p in text_lower for p in cmd_phrases)


# ─── Graph Nodes ─────────────────────────────────────────────────────────────

def classify_intent_node(state: AgentState) -> dict:
    """Node: Classify intent and auto-extract platform if mentioned."""
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "other"}

    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # ── Mid-flow escape: allow user to ask product questions or greet ────
    # If the user is in lead flow but sends a product query or greeting,
    # exit lead flow and reset fields so they can re-enter later.
    if state.get("in_lead_flow") and not is_lead_complete(state):
        escape_intent = _rule_based_intent(user_text)
        if escape_intent in ("product_query", "greeting"):
            logger.info(f"User escaped lead flow with intent: {escape_intent}")
            return {
                "intent": escape_intent,
                "in_lead_flow": False,
                "name": None,
                "email": None,
                "platform": None,
            }

        # Normal in-flow field detection
        missing = get_missing_lead_field(state)
        if missing == "email" and _extract_email(user_text):
            return {"intent": "provide_email"}
        elif missing == "name":
            return {"intent": "provide_name"}
        elif missing == "platform":
            return {"intent": "provide_platform"}

    # Standard intent classification
    intent = _rule_based_intent(user_text)

    # Auto-extract platform from high-intent messages
    # e.g. "I want Pro plan for my YouTube channel" → platform="YouTube"
    updates = {"intent": intent}
    if intent == "high_intent":
        platform = extract_platform(user_text)
        if platform:
            updates["platform"] = platform

    return updates


def greeting_node(state: AgentState) -> dict:
    """Node: Handle greetings — LLM generates the response."""
    response = _invoke_llm_with_retry([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="Say a short friendly greeting as AutoStream's assistant. Mention you can help with plans and pricing.")
    ])
    return {"messages": [AIMessage(content=response.content)]}


def product_query_node(state: AgentState) -> dict:
    """Node: Answer product questions using RAG context."""
    messages = state.get("messages", [])
    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # Retrieve relevant context from knowledge base
    context = retrieve_context(user_text)
    system = SYSTEM_PROMPT + f"\n\n--- KNOWLEDGE BASE ---\n{context}\n--- END ---\nAnswer ONLY from the knowledge base above. Do not invent information."

    # Build message list with recent history
    chat_messages = [SystemMessage(content=system)]
    for m in messages[-6:]:
        if isinstance(m, HumanMessage):
            chat_messages.append(m)
        elif isinstance(m, AIMessage):
            chat_messages.append(m)

    response = _invoke_llm_with_retry(chat_messages)
    return {"messages": [AIMessage(content=response.content)]}


def lead_flow_node(state: AgentState) -> dict:
    """Node: Handle lead collection step by step.

    Flow:
      - high_intent detected → platform may be auto-extracted → ask for name
      - name provided → ask for email
      - email provided → if platform missing, ask for it; else tool fires
    """
    messages = state.get("messages", [])
    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    intent = state.get("intent", "")

    updates = {"in_lead_flow": True}
    missing = get_missing_lead_field(state)

    # ── Step 1: Collect name ─────────────────────────────────────────────
    if missing == "name":
        if intent == "provide_name" and not _looks_like_command(user_text):
            updates["name"] = user_text.strip().title()
            logger.info(f"Name captured: {updates['name']}")
            response = _invoke_llm_with_retry([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"The user's name is {updates['name']}. Acknowledge warmly and ask for their email address. Keep it short.")
            ])
            updates["messages"] = [AIMessage(content=response.content)]
        else:
            # First entry into lead flow — ask for name
            platform = state.get("platform", "")
            platform_note = f" for their {platform} channel" if platform else ""
            response = _invoke_llm_with_retry([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"The user wants to try AutoStream Pro{platform_note}. Express excitement and ask for their name to get started. Keep it short.")
            ])
            updates["messages"] = [AIMessage(content=response.content)]

    # ── Step 2: Collect email ────────────────────────────────────────────
    elif missing == "email":
        email = _extract_email(user_text)
        if email:
            updates["email"] = email
            logger.info(f"Email captured: {email}")
            # If platform is already known → don't ask, tool_capture handles it
            # If platform is missing → ask for it
            if not state.get("platform"):
                response = _invoke_llm_with_retry([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"Got the email. Now ask which creator platform they use (YouTube, Instagram, Twitch, TikTok, etc.). Keep it short.")
                ])
                updates["messages"] = [AIMessage(content=response.content)]
        else:
            name = state.get("name", "")
            response = _invoke_llm_with_retry([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"The user ({name}) provided '{user_text}' but it doesn't look like a valid email. Kindly ask for a valid email address (e.g., name@example.com).")
            ])
            updates["messages"] = [AIMessage(content=response.content)]

    # ── Step 3: Collect platform (only if not auto-extracted) ────────────
    elif missing == "platform":
        updates["platform"] = user_text.strip().title()
        logger.info(f"Platform captured: {updates['platform']}")
        # No message needed — tool_capture_node will generate the confirmation

    return updates


def tool_capture_node(state: AgentState) -> dict:
    """Node: Execute mock_lead_capture ONLY after all 3 fields are collected.
    This node is ONLY reached when check_lead_complete returns 'tool_capture'."""
    name = state.get("name", "")
    email = state.get("email", "")
    platform = state.get("platform", "")

    # Call the tool — guarded by check_lead_complete conditional edge
    result = mock_lead_capture.invoke({"name": name, "email": email, "platform": platform})
    logger.info(f"Lead captured: {name}, {email}, {platform}")

    # LLM generates confirmation
    response = _invoke_llm_with_retry([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Lead captured! Name: {name}, Email: {email}, Platform: {platform}. "
            f"Generate a short, enthusiastic confirmation. Tell them the team will reach out "
            f"to {email} shortly. Welcome them to AutoStream and mention their {platform} channel."
        ))
    ])

    return {
        "lead_captured": True,
        "in_lead_flow": False,
        "messages": [AIMessage(content=response.content)],
    }


def general_node(state: AgentState) -> dict:
    """Node: Handle general/other queries."""
    messages = state.get("messages", [])

    chat_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in messages[-6:]:
        if isinstance(m, HumanMessage):
            chat_messages.append(m)
        elif isinstance(m, AIMessage):
            chat_messages.append(m)

    response = _invoke_llm_with_retry(chat_messages)
    return {"messages": [AIMessage(content=response.content)]}


# ─── Routing Functions ───────────────────────────────────────────────────────

def route_by_intent(state: AgentState) -> str:
    """Conditional edge: route based on intent."""
    intent = state.get("intent", "other")

    # Stay in lead flow if active and incomplete
    if state.get("in_lead_flow") and not is_lead_complete(state):
        return "lead_flow"

    if intent == "greeting":
        return "greeting"
    elif intent == "product_query":
        return "product_query"
    elif intent in ("high_intent", "provide_name", "provide_email", "provide_platform"):
        return "lead_flow"
    else:
        return "general"


def check_lead_complete(state: AgentState) -> str:
    """Conditional edge: tool fires ONLY when all 3 fields are present."""
    if is_lead_complete(state):
        return "tool_capture"
    return END


# ─── Build the Graph ─────────────────────────────────────────────────────────

def build_graph():
    """Construct and compile the LangGraph StateGraph."""
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("greeting", greeting_node)
    builder.add_node("product_query", product_query_node)
    builder.add_node("lead_flow", lead_flow_node)
    builder.add_node("tool_capture", tool_capture_node)
    builder.add_node("general", general_node)

    # Entry: every message starts with intent classification
    builder.add_edge(START, "classify_intent")

    # Route to handler based on classified intent
    builder.add_conditional_edges("classify_intent", route_by_intent, {
        "greeting": "greeting",
        "product_query": "product_query",
        "lead_flow": "lead_flow",
        "general": "general",
    })

    # Terminal edges
    builder.add_edge("greeting", END)
    builder.add_edge("product_query", END)
    builder.add_edge("general", END)

    # Lead flow → check if all 3 fields → tool or end
    builder.add_conditional_edges("lead_flow", check_lead_complete, {
        "tool_capture": "tool_capture",
        END: END,
    })
    builder.add_edge("tool_capture", END)

    # WARNING: MemorySaver stores all sessions in-memory and grows unbounded.
    # For production, replace with SqliteSaver or a DB-backed checkpointer.
    # See: https://langchain-ai.github.io/langgraph/reference/checkpoints/
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


# ─── Module-level graph ──────────────────────────────────────────────────────
graph = build_graph()


def process_message(user_message: str, thread_id: str = "default") -> dict:
    """Main entry point — send a message, get the agent's reply.
    Uses thread_id for multi-turn memory via LangGraph checkpointer."""
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config,
    )

    # Extract the last AI message
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    reply = ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't process that."

    return {
        "reply": reply,
        "state": {
            "intent": result.get("intent", ""),
            "name": result.get("name"),
            "email": result.get("email"),
            "platform": result.get("platform"),
            "in_lead_flow": result.get("in_lead_flow", False),
            "lead_captured": result.get("lead_captured", False),
            "message_count": len(result.get("messages", [])),
        }
    }