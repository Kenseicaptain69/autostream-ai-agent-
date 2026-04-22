"""
app.py — AutoStream AI Frontend
Clean dark glassmorphism UI — content-safe layout.
"""

import os
import time
import uuid
import requests
import streamlit as st

st.set_page_config(
    page_title="AutoStream AI",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="expanded",
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
}

/* Dark gradient background — NO pseudo-elements that block content */
.stApp {
    background: radial-gradient(ellipse at 10% 10%, rgba(110,70,240,0.22) 0%, transparent 45%),
                radial-gradient(ellipse at 90% 90%, rgba(30,100,255,0.18) 0%, transparent 45%),
                linear-gradient(160deg, #07070f 0%, #0b0d1c 50%, #070b18 100%) !important;
    background-attachment: fixed !important;
}

/* Main block */
.main .block-container {
    max-width: 800px;
    padding: 1.5rem 2rem 8rem 2rem;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: rgba(15, 12, 30, 0.92) !important;
    border-right: 1px solid rgba(139, 92, 246, 0.15) !important;
}
section[data-testid="stSidebar"] > div {
    background: transparent !important;
}

/* ── All Streamlit text → white ── */
.stApp, .stApp p, .stApp span, .stApp div, .stApp label {
    color: #e2e8f0 !important;
}

/* ── Chat messages — user ── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, rgba(109,40,217,0.55), rgba(67,56,202,0.45)) !important;
    border: 1px solid rgba(139,92,246,0.4) !important;
    border-radius: 20px 20px 5px 20px !important;
    box-shadow: 0 4px 20px rgba(109,40,217,0.3) !important;
    color: #fff !important;
    backdrop-filter: blur(16px) !important;
}

/* ── Chat messages — agent ── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 20px 20px 20px 5px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
    color: #e2e8f0 !important;
    backdrop-filter: blur(16px) !important;
}

[data-testid="stChatMessageContent"] {
    font-size: 0.92rem !important;
    line-height: 1.65 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Avatars */
[data-testid="chatAvatarIcon-user"] {
    background: linear-gradient(135deg, rgba(139,92,246,0.6), rgba(67,56,202,0.5)) !important;
    border: 1px solid rgba(139,92,246,0.5) !important;
    border-radius: 50% !important;
}
[data-testid="chatAvatarIcon-assistant"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 50% !important;
}

/* ── Chat input area ── */
[data-testid="stBottom"] > div,
.stChatFloatingInputContainer > div {
    background: rgba(7,7,20,0.92) !important;
    border-top: 1px solid rgba(139,92,246,0.18) !important;
    backdrop-filter: blur(24px) !important;
}
div[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(139,92,246,0.25) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(16px) !important;
}
div[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #e2e8f0 !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    caret-color: #a78bfa !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(226,232,240,0.35) !important;
}
div[data-testid="stChatInput"] button {
    background: rgba(139,92,246,0.35) !important;
    border: 1px solid rgba(139,92,246,0.4) !important;
    border-radius: 9px !important;
    color: #fff !important;
}
div[data-testid="stChatInput"] button:hover {
    background: rgba(139,92,246,0.6) !important;
    box-shadow: 0 4px 16px rgba(139,92,246,0.35) !important;
}

/* ── Sidebar buttons ── */
.stButton > button {
    background: rgba(255,255,255,0.05) !important;
    color: rgba(226,232,240,0.8) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    padding: 0.45rem 0.75rem !important;
}
.stButton > button:hover {
    background: rgba(139,92,246,0.18) !important;
    border-color: rgba(139,92,246,0.4) !important;
    color: #fff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(139,92,246,0.22) !important;
}
button[kind="secondary"] {
    background: rgba(239,68,68,0.08) !important;
    border-color: rgba(239,68,68,0.2) !important;
    color: rgba(252,165,165,0.85) !important;
}
button[kind="secondary"]:hover {
    background: rgba(239,68,68,0.18) !important;
    border-color: rgba(239,68,68,0.4) !important;
    color: #fca5a5 !important;
}

/* ── Spinner text ── */
[data-testid="stSpinner"] p { color: #a78bfa !important; }

/* ── Hide branding ── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "lead_captured" not in st.session_state:
    st.session_state.lead_captured = False
if "backend_ok" not in st.session_state:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        st.session_state.backend_ok = r.status_code == 200
    except Exception:
        st.session_state.backend_ok = False


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎥 AutoStream AI")
    st.caption("Intelligent Sales Assistant · Gemini Powered")
    st.divider()

    # Status
    if st.session_state.backend_ok:
        st.success("🟢 Backend Online", icon=None)
    else:
        st.error("🔴 Backend Offline", icon=None)

    st.divider()

    # Session stats
    st.markdown("**📊 Session**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", len(st.session_state.messages))
    with col2:
        st.metric("Lead", "✅" if st.session_state.lead_captured else "❌")

    sid_short = st.session_state.session_id[:16] + "…"
    st.caption(f"ID: `{sid_short}`")

    st.divider()

    # Quick prompts
    st.markdown("**💡 Quick Prompts**")
    prompts = [
        ("💰", "What are your pricing plans?"),
        ("⚡", "Tell me about the Pro plan"),
        ("🎬", "AutoStream for YouTube"),
        ("🔧", "What features do you offer?"),
    ]
    for emoji, label in prompts:
        if st.button(f"{emoji} {label}", use_container_width=True, key=f"qp_{label}"):
            st.session_state["_quick"] = label
            st.rerun()

    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.lead_captured = False
        st.rerun()


# ─── Hero Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 1.4rem;">
    <div style="
        display:inline-flex; align-items:center; justify-content:center;
        width:68px; height:68px; border-radius:18px;
        background:rgba(139,92,246,0.18);
        border:1px solid rgba(139,92,246,0.35);
        font-size:1.9rem; margin-bottom:1rem;
        box-shadow: 0 0 40px rgba(139,92,246,0.25);
    ">🎥</div>
    <h1 style="
        font-size:2rem; font-weight:800; letter-spacing:-0.5px; margin:0;
        background: linear-gradient(135deg, #ffffff 20%, #c4b5fd 60%, #93c5fd 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        background-clip:text;
    ">AutoStream AI</h1>
    <p style="color:rgba(226,232,240,0.45); font-size:0.88rem; margin:0.5rem 0 0.9rem;">
        Your intelligent sales companion · Powered by Gemini
    </p>
    <div style="
        display:inline-flex; align-items:center; gap:8px;
        padding:5px 16px; border-radius:999px;
        background:rgba(139,92,246,0.1);
        border:1px solid rgba(139,92,246,0.25);
        font-size:0.76rem; color:rgba(226,232,240,0.65);
    ">
        <span style="
            width:7px;height:7px;border-radius:50%;
            background:#4ade80;display:inline-block;
        "></span>
        AI Online &nbsp;·&nbsp; Ask me anything
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border:none;border-top:1px solid rgba(139,92,246,0.15);margin:0 0 1.2rem;'>", unsafe_allow_html=True)


# ─── Chat History ─────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem;">
        <div style="font-size:2.5rem; margin-bottom:0.8rem;">✨</div>
        <p style="font-size:1rem; font-weight:600; color:rgba(226,232,240,0.7); margin-bottom:0.4rem;">
            Start a conversation
        </p>
        <p style="font-size:0.83rem; color:rgba(226,232,240,0.32); line-height:1.7;">
            Ask about plans, features, or pricing.<br>
            I'm here to help you get started with AutoStream.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        role   = "user" if msg["role"] == "user" else "assistant"
        avatar = "👤" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.write(msg["content"])
            if msg.get("lead_captured"):
                st.success("🎉 Lead captured — our team will reach out to you shortly!")


# ─── Send Logic ───────────────────────────────────────────────────────────────
def send(user_text: str):
    ts = time.strftime("%I:%M %p")
    st.session_state.messages.append({"role": "user", "content": user_text, "time": ts})

    try:
        with st.spinner("AutoStream AI is thinking…"):
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": user_text, "session_id": st.session_state.session_id},
                timeout=30,
            )
        if resp.status_code == 200:
            data     = resp.json()
            reply    = data.get("reply", "Sorry, I couldn't process that.")
            captured = data.get("lead_captured", False)
            st.session_state.lead_captured = captured
            st.session_state.messages.append({
                "role": "agent", "content": reply,
                "time": ts, "lead_captured": captured,
            })
        else:
            st.session_state.messages.append({
                "role": "agent",
                "content": f"⚠️ Backend error {resp.status_code}. Please try again.",
                "time": ts,
            })
    except requests.exceptions.ConnectionError:
        st.session_state.messages.append({
            "role": "agent",
            "content": "⚠️ Cannot reach backend. Make sure uvicorn is running in venv.",
            "time": ts,
        })
    except Exception as e:
        st.session_state.messages.append({
            "role": "agent", "content": f"⚠️ Error: {e}", "time": ts,
        })
    st.rerun()


# ─── Quick prompt ──────────────────────────────────────────────────────────────
if "_quick" in st.session_state and st.session_state["_quick"]:
    p = st.session_state.pop("_quick")
    send(p)

# ─── Input ─────────────────────────────────────────────────────────────────────
if user_input := st.chat_input("Ask about plans, pricing, or get started…"):
    send(user_input)
