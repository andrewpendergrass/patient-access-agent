# Patient Access Triage Agent

An AI agent that helps healthcare access teams handle inbound patient requests — classifying intent, checking for medical escalation risk, retrieving context from a mock knowledge base, drafting responses, and logging every decision to an auditable case record.

## Architecture

```
React Frontend (Vite + Tailwind)
        ↓  SSE stream
FastAPI Backend
        ↓
LangGraph Agent Orchestrator
        ↓
┌───────────────────────────────────────────────┐
│ triage_node     → classifies intent + risk    │
│ emergency_node  → safety protocol (rule-based)│
│ provider_lookup → mock provider directory     │
│ appointment     → mock scheduling policies    │
│ insurance       → mock coverage database      │
│ synthesize      → draft response + summary    │
│ log             → SQLite audit trail          │
└───────────────────────────────────────────────┘
        ↓
Anthropic Claude (LLM calls in triage + synthesize)
```

**Key design choices:**
- LangGraph `StateGraph` for explicit, inspectable DAG routing (not a black-box ReAct loop)
- SSE streaming so every agent step surfaces in real time in the UI
- Emergency detection happens in the triage LLM call — no special-cased keywords — then the graph hard-routes to the safety protocol node
- All data is mock; no real PHI is used

## Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Copy and fill in your API key
cp ../.env.example .env
# Edit .env and set ANTHROPIC_API_KEY

python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Demo Flow

**Emergency escalation:**
> "I need to reschedule my cardiology appointment and I've been having chest tightness for the past hour."

Watch the agent detect emergency risk in the triage step, route to the emergency protocol node, skip scheduling, issue safety guidance, then log the escalated case.

**Provider lookup:**
> "I need to find a Spanish-speaking pediatrician near Lee's Summit who takes Aetna."

Watch the agent classify intent, filter the mock provider directory by specialty + language + insurance + location, draft a patient-facing response with matching providers, generate a case summary, and log to audit.

## Project Structure

```
patient-access-agent/
├── backend/
│   ├── main.py              # FastAPI app + SSE endpoint
│   ├── database.py          # SQLite audit log
│   ├── agent/
│   │   ├── graph.py         # LangGraph StateGraph
│   │   ├── nodes.py         # Node implementations
│   │   ├── prompts.py       # LLM prompt templates
│   │   └── state.py         # AgentState TypedDict
│   └── data/
│       ├── providers.json   # Mock provider directory
│       ├── policies.json    # Mock clinic policies
│       └── insurance.json   # Mock insurance coverage
└── frontend/
    └── src/
        ├── App.tsx
        ├── api.ts           # SSE streaming client
        └── components/
            ├── AgentTrace.tsx   # Step-by-step reasoning UI
            ├── ResponsePanel.tsx
            └── AuditLog.tsx
```
