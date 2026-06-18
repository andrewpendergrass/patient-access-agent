import json
import os
import sys  # noqa: F401  kept for stderr writes
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

_has_key = os.getenv("ANTHROPIC_API_KEY", "").strip().startswith("sk-")
if not _has_key:
    print("INFO: No ANTHROPIC_API_KEY found — running in demo/mock mode.", file=sys.stderr)

from database import init_db, get_cases
from agent import agent_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Patient Access Triage Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    request: str


@app.post("/api/process")
async def process_request(body: ProcessRequest):
    if not body.request.strip():
        raise HTTPException(status_code=400, detail="Request cannot be empty")

    initial_state = {
        "request": body.request.strip(),
        "intent": "",
        "risk_level": "low",
        "entities": {},
        "retrieved_data": {},
        "steps": [],
        "draft_response": "",
        "case_summary": {},
        "case_id": "",
    }

    async def stream_agent():
        seen_steps = 0
        final_state = {}

        async for event in agent_graph.astream(initial_state):
            for node_name, node_output in event.items():
                if node_output is None:
                    continue

                # Emit any new steps
                steps = node_output.get("steps", [])
                for step in steps[seen_steps:]:
                    payload = json.dumps({"type": "step", "data": step})
                    yield {"data": payload}
                seen_steps = len(steps)

                # Track final state
                final_state.update(node_output)

        # Emit final result
        result = {
            "type": "result",
            "data": {
                "response": final_state.get("draft_response", ""),
                "case_summary": final_state.get("case_summary", {}),
                "case_id": final_state.get("case_id", ""),
                "risk_level": final_state.get("risk_level", "low"),
                "intent": final_state.get("intent", "general"),
                "retrieved_data": final_state.get("retrieved_data", {}),
            },
        }
        yield {"data": json.dumps(result)}

    return EventSourceResponse(stream_agent())


@app.get("/api/cases")
async def list_cases(limit: int = 50):
    cases = await get_cases(limit=limit)
    return {"cases": cases}


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")}
