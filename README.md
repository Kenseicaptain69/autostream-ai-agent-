# AutoStream AI Agent 🎥

An intelligent SaaS sales assistant powered by **LangGraph + Gemini 2.5 Flash**.
Handles product queries via RAG, captures leads through natural conversation, and supports multi-turn memory.

---

## Setup

**1. Install Dependencies**

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r Requirements.txt
```

**2. Add Your API Key**

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your-google-api-key-here
```

Get a free key → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## Run

Open **two terminals** (venv activated in both):

| Terminal | Command | URL |
|----------|---------|-----|
| 1 — Backend | `uvicorn main:app --reload --port 8000` | http://localhost:8000 |
| 2 — Frontend | `streamlit run app.py` | http://localhost:8501 |

---

## How It Works

| Step | You Say | Agent Does |
|------|---------|------------|
| 1 | *"What are your pricing plans?"* | Answers from knowledge base (RAG) |
| 2 | *"I want the Pro plan for YouTube"* | Detects buying intent, extracts platform |
| 3 | *"shreeyash"* | Captures name, asks for email |
| 4 | *"shreemobarkar@example.com"* | Captures email, saves lead to `leads.json` |

---

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | FastAPI backend — `/chat`, `/health`, `/session` endpoints |
| `app.py` | Streamlit frontend — dark glassmorphism chat UI |
| `agent.py` | LangGraph StateGraph — core agent logic |
| `intent.py` | Rule-based intent classification |
| `rag.py` | Knowledge base retrieval |
| `tools.py` | Lead capture tool (`@tool` decorator) |
| `state.py` | LangGraph state schema |
| `Knowledge.json` | Product knowledge base (plans, pricing, policies) |
| `leads.json` | Captured leads storage |
| `Requirements.txt` | Python dependencies |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message, get agent reply |
| `GET` | `/health` | Backend health check |
| `GET` | `/session/{id}` | Get session state |

---

## Testing

```bash
python test_logic.py            # Quick logic check (no API calls)
python -m pytest tests/ -v      # Full test suite (90 tests)
```