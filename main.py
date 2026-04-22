"""
main.py — FastAPI server for AutoStream AI Agent
Uses LangGraph-powered agent with Gemini 2.5 Flash and multi-turn memory.
"""

import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from agent import process_message, graph
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

app = FastAPI(title="AutoStream AI Agent", version="2.0.0")

# CORS — configurable via CORS_ORIGINS env var (comma-separated), defaults to "*" for dev
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    state: dict
    lead_captured: bool


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the AutoStream agent."""
    session_id = req.session_id or "default"

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = process_message(req.message, thread_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(
        reply=result["reply"],
        session_id=session_id,
        state=result["state"],
        lead_captured=result["state"].get("lead_captured", False),
    )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get the current state of a conversation session."""
    config = {"configurable": {"thread_id": session_id}}
    try:
        snapshot = graph.get_state(config)
        if snapshot and snapshot.values:
            state = snapshot.values
            return {
                "intent": state.get("intent", ""),
                "name": state.get("name"),
                "email": state.get("email"),
                "in_lead_flow": state.get("in_lead_flow", False),
                "lead_captured": state.get("lead_captured", False),
                "message_count": len(state.get("messages", [])),
            }
        raise HTTPException(status_code=404, detail="Session not found.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found.")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "AutoStream AI",
        "llm": "Gemini 2.5 Flash",
        "framework": "LangGraph",
    }


# ─── CLI Test Mode ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uuid

    print("AutoStream AI Agent - CLI Test Mode")
    print("Powered by LangGraph + Gemini 2.5 Flash")
    print("Type 'quit' to exit | 'reset' to start new session\n")

    thread_id = str(uuid.uuid4())
    print(f"[Session: {thread_id[:8]}...]\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            thread_id = str(uuid.uuid4())
            print(f"[Session reset: {thread_id[:8]}...]\n")
            continue

        try:
            result = process_message(user_input, thread_id=thread_id)
            print(f"Agent: {result['reply']}")
            print(f"  [intent={result['state']['intent']} | lead_flow={result['state']['in_lead_flow']} | captured={result['state']['lead_captured']}]\n")
        except Exception as e:
            print(f"[Error] {e}\n")