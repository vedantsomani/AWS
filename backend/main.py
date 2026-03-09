"""FastAPI backend — multi-agent orchestrator entry point."""

from __future__ import annotations

import json
import logging
import os
import traceback
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from auth import get_user_id_from_token, get_ws_user_id
from bedrock_models import BEDROCK_MODELS
from build_host import build_and_deploy, generate_only, deploy_only
from graph.orchestrator import RECURSION_LIMIT, State, build_graph

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CodeSaaS Orchestrator",
    version="0.2.0",
    description="Multi-agent coding orchestrator powered by LangGraph.",
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
        headers={"Retry-After": "3600"},
    )


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Health check — verifies the server is up and key env vars are set."""
    checks: dict[str, str] = {"server": "ok"}

    if os.getenv("OPENAI_API_KEY"):
        checks["llm"] = "configured"
    else:
        checks["llm"] = "missing OPENAI_API_KEY"

    if os.getenv("E2B_API_KEY"):
        checks["sandbox"] = "configured"
    else:
        checks["sandbox"] = "missing E2B_API_KEY"

    return checks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AGENT_DISPLAY_NAMES: dict[str, str] = {
    "supervisor": "Supervisor",
    "frontend_agent": "Frontend Agent",
    "backend_agent": "Backend Agent",
    "database_agent": "Database Agent",
    "devops_agent": "DevOps Agent",
    "integration_agent": "Integration Agent",
    "qa_agent": "QA Agent",
    "increment_iteration": "Retry Controller",
}


def _serialise_message(msg: BaseMessage) -> dict[str, str]:
    content = msg.content if isinstance(msg.content, str) else str(msg.content)
    return {"role": msg.type, "content": content}


def _make_initial_state(prompt: str) -> State:
    return {
        "messages": [HumanMessage(content=prompt)],
        "current_task": "planning",
        "plan": "",
        "supervisor_plan": {},
        "agents_needed": [],
        "frontend_files": [],
        "backend_files": [],
        "database_files": [],
        "devops_files": [],
        "files": [],
        "run_command": "",
        "terminal_output": "",
        "execution_success": False,
        "preview_url": "",
        "qa_verdict": {},
        "iteration": 0,
        "max_iterations": RECURSION_LIMIT,
    }


def _serialise_state_snapshot(state: dict) -> dict:
    messages = state.get("messages", [])
    serialised_msgs = [
        _serialise_message(m) if isinstance(m, BaseMessage) else m
        for m in messages
    ] if messages else []

    return {
        "messages": serialised_msgs,
        "current_task": state.get("current_task", ""),
        "plan": state.get("plan", ""),
        "agents_needed": state.get("agents_needed", []),
        "files": state.get("files", []),
        "frontend_files": state.get("frontend_files", []),
        "backend_files": state.get("backend_files", []),
        "database_files": state.get("database_files", []),
        "devops_files": state.get("devops_files", []),
        "run_command": state.get("run_command", ""),
        "terminal_output": state.get("terminal_output", ""),
        "execution_success": state.get("execution_success", False),
        "preview_url": state.get("preview_url", ""),
        "qa_verdict": state.get("qa_verdict", {}),
        "iteration": state.get("iteration", 0),
    }


# ---------------------------------------------------------------------------
# REST endpoint
# ---------------------------------------------------------------------------


class RunAgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)


class MessageOut(BaseModel):
    role: str
    content: str


class CodeFileOut(BaseModel):
    path: str
    content: str


class RunAgentResponse(BaseModel):
    messages: list[MessageOut]
    current_task: str
    plan: str
    files: list[CodeFileOut]
    run_command: str
    terminal_output: str
    execution_success: bool
    preview_url: str
    agents_needed: list[str]
    iteration: int


@app.post("/api/run-agent", response_model=RunAgentResponse)
@limiter.limit("10/hour")
async def run_agent(request: Request, payload: RunAgentRequest) -> RunAgentResponse:
    """Trigger the multi-agent pipeline and return the final state."""
    request_id = str(uuid.uuid4())[:8]
    logger.info("[%s] Starting agent pipeline for prompt: %s...", request_id, payload.prompt[:80])

    graph = build_graph()
    initial_state = _make_initial_state(payload.prompt.strip())

    try:
        final_state: State = graph.invoke(
            initial_state,
            {"recursion_limit": RECURSION_LIMIT * 6},
        )
    except Exception as exc:
        logger.error("[%s] Agent pipeline failed: %s", request_id, exc)
        raise HTTPException(status_code=502, detail=f"Agent execution failed: {exc}") from exc

    serialised = _serialise_state_snapshot(final_state)

    return RunAgentResponse(
        messages=[MessageOut(**m) for m in serialised["messages"]],
        current_task=serialised["current_task"],
        plan=serialised.get("plan", ""),
        files=[
            CodeFileOut(path=f.get("path", f.get("filename", "")), content=f.get("content", ""))
            for f in serialised.get("files", [])
        ],
        run_command=serialised.get("run_command", ""),
        terminal_output=serialised.get("terminal_output", ""),
        execution_success=serialised.get("execution_success", False),
        preview_url=serialised.get("preview_url", ""),
        agents_needed=serialised.get("agents_needed", []),
        iteration=serialised.get("iteration", 0),
    )


# ---------------------------------------------------------------------------
# WebSocket Streaming
# ---------------------------------------------------------------------------


@app.websocket("/ws/agent")
async def ws_agent(ws: WebSocket, token: str | None = Query(default=None)) -> None:
    """Stream multi-agent execution over WebSocket.

    Protocol:
      {"type": "agent_start", "agent": "Frontend Agent", "node": "frontend_agent"}
      {"type": "node_update", "node": "...", "agent": "...", "state": {...}}
      {"type": "agent_complete", "agent": "...", "node": "...", "files_count": N}
      {"type": "final", "state": {...}}
      {"type": "error", "detail": "..."}
    """
    await ws.accept()
    request_id = str(uuid.uuid4())[:8]

    # Optional JWT auth (non-blocking in dev when SUPABASE_JWT_SECRET is unset)
    user_id = await get_ws_user_id(ws, token)

    try:
        raw = await ws.receive_text()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await ws.send_json({"type": "error", "detail": "Invalid JSON payload."})
            await ws.close(code=1003)
            return

        prompt: str | None = payload.get("prompt")
        if not prompt or not isinstance(prompt, str) or len(prompt.strip()) == 0:
            await ws.send_json({"type": "error", "detail": "Missing or empty 'prompt' field."})
            await ws.close(code=1003)
            return

        if len(prompt) > 10_000:
            await ws.send_json({"type": "error", "detail": "Prompt exceeds 10,000 character limit."})
            await ws.close(code=1003)
            return

        logger.info("[%s] WS agent start (user=%s): %s...", request_id, user_id or "anon", prompt[:80])

        graph = build_graph()
        initial_state = _make_initial_state(prompt.strip())

        final_state: dict = {}

        async for event in graph.astream(
            initial_state,
            {"recursion_limit": RECURSION_LIMIT * 6},
            stream_mode="updates",
        ):
            for node_name, node_output in event.items():
                agent_display = AGENT_DISPLAY_NAMES.get(node_name, node_name)

                await ws.send_json({
                    "type": "agent_start",
                    "agent": agent_display,
                    "node": node_name,
                })

                serialisable: dict = {}
                for key, value in node_output.items():
                    if key == "messages" and isinstance(value, list):
                        serialisable[key] = [
                            _serialise_message(m) if isinstance(m, BaseMessage) else m
                            for m in value
                        ]
                    else:
                        serialisable[key] = value

                await ws.send_json({
                    "type": "node_update",
                    "node": node_name,
                    "agent": agent_display,
                    "state": serialisable,
                })

                node_files = (
                    serialisable.get("files")
                    or serialisable.get("frontend_files")
                    or serialisable.get("backend_files")
                    or serialisable.get("database_files")
                    or serialisable.get("devops_files")
                    or []
                )

                complete_frame: dict = {
                    "type": "agent_complete",
                    "agent": agent_display,
                    "node": node_name,
                    "files_count": len(node_files),
                }

                # Include preview_url in agent_complete when available (from QA)
                if serialisable.get("preview_url"):
                    complete_frame["preview_url"] = serialisable["preview_url"]

                await ws.send_json(complete_frame)

                final_state.update(serialisable)

        await ws.send_json({
            "type": "final",
            "state": final_state,
        })

        await ws.close(code=1000)
        logger.info("[%s] WS agent complete.", request_id)

    except WebSocketDisconnect:
        logger.info("[%s] WebSocket client disconnected.", request_id)

    except Exception as exc:
        logger.error("[%s] WebSocket error: %s\n%s", request_id, exc, traceback.format_exc())
        try:
            await ws.send_json({"type": "error", "detail": str(exc)})
            await ws.close(code=1011)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# Build & Host Mode — separate from multi-agent IDE
# ═══════════════════════════════════════════════════════════════════════


@app.get("/api/bedrock-models")
async def list_bedrock_models() -> list[dict]:
    """Available Bedrock models for the Build & Host frontend."""
    return [{k: v for k, v in m.items() if k != "model_id"} for m in BEDROCK_MODELS]


class BuildRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)
    model: str = Field(default="amazon-nova-pro")


class DeployRequest(BaseModel):
    html: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1, max_length=500)


@app.post("/api/generate")
async def api_generate(request: Request, payload: BuildRequest) -> dict:
    """Step 1 — Generate HTML via Bedrock. No deployment."""
    rid = str(uuid.uuid4())[:8]
    logger.info("[%s] Generate model=%s prompt=%s...", rid, payload.model, payload.prompt[:60])

    try:
        result = generate_only(payload.prompt.strip(), payload.model)
    except Exception as exc:
        logger.error("[%s] Generate failed: %s", rid, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    html = result.get("html", "")
    return {
        "html": html,
        "html_length": len(html),
        "model_used": result.get("model", payload.model),
    }


@app.post("/api/deploy")
async def api_deploy(request: Request, payload: DeployRequest) -> dict:
    """Step 2 — Deploy pre-generated HTML to Vercel."""
    rid = str(uuid.uuid4())[:8]
    logger.info("[%s] Deploy prompt=%s...", rid, payload.prompt[:60])

    try:
        result = deploy_only(payload.html, payload.prompt.strip())
    except Exception as exc:
        logger.error("[%s] Deploy failed: %s", rid, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "deploy_url": result.get("deploy_url", ""),
        "deploy_id": result.get("deploy_id", ""),
    }


@app.post("/api/build-and-host")
async def api_build_host(request: Request, payload: BuildRequest) -> dict:
    """Legacy: Generate + deploy in one call."""
    rid = str(uuid.uuid4())[:8]
    logger.info("[%s] Build&Host model=%s prompt=%s...", rid, payload.model, payload.prompt[:60])

    try:
        result = build_and_deploy(payload.prompt.strip(), payload.model)
    except Exception as exc:
        logger.error("[%s] Build failed: %s", rid, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    html = result.get("html", "")
    return {
        "deploy_url": result.get("deploy_url", ""),
        "deploy_error": result.get("deploy_error", ""),
        "model_used": result.get("model", payload.model),
        "html_length": len(html),
        "html": html,
    }
