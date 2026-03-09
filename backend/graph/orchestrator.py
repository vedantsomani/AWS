"""LangGraph orchestrator — multi-agent supervisor/workers pipeline."""

from __future__ import annotations

import logging
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from agents.supervisor import supervisor
from agents.frontend_agent import frontend_agent
from agents.backend_agent import backend_agent
from agents.database_agent import database_agent
from agents.devops_agent import devops_agent
from agents.integration_agent import integration_agent
from agents.qa_agent import qa_agent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------


class State(TypedDict):
    """Shared state flowing through the multi-agent graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    current_task: str

    # Supervisor outputs
    plan: str
    supervisor_plan: dict  # serialized SupervisorPlan
    agents_needed: list[str]  # ["frontend", "backend", "database", "devops"]

    # Per-agent file outputs
    frontend_files: list[dict[str, str]]
    backend_files: list[dict[str, str]]
    database_files: list[dict[str, str]]
    devops_files: list[dict[str, str]]

    # Integration output (merged)
    files: list[dict[str, str]]  # merged file tree — used by executor + frontend
    run_command: str

    # QA results
    terminal_output: str
    execution_success: bool
    preview_url: str
    qa_verdict: dict  # serialized QAVerdict

    # Loop control
    iteration: int
    max_iterations: int


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

RECURSION_LIMIT = 5


def _route_after_qa(state: State) -> str:
    """After QA: end if passed or max iterations reached, else retry."""
    qa_verdict = state.get("qa_verdict", {})
    passed = qa_verdict.get("passed", False) if isinstance(qa_verdict, dict) else False
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", RECURSION_LIMIT)

    if passed:
        return "end"
    if iteration >= max_iter:
        logger.warning("Max iterations (%d) reached — ending.", max_iter)
        return "end"
    return "retry"


def _increment_iteration(state: State) -> dict:
    """Bump iteration counter before re-entering supervisor."""
    return {
        "iteration": state.get("iteration", 0) + 1,
        "current_task": "retrying",
    }


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Build the multi-agent supervisor → workers → integration → QA graph.

    Flow:
        supervisor → frontend_agent → backend_agent → database_agent → devops_agent
                   → integration_agent → qa_agent
                   → (pass) END
                   → (fail) increment_iteration → supervisor (retry)

    Worker agents self-skip when not in agents_needed list.
    Sequential execution ensures stable state between agents.
    """
    graph = StateGraph(State)

    # Nodes
    graph.add_node("supervisor", supervisor)
    graph.add_node("frontend_agent", frontend_agent)
    graph.add_node("backend_agent", backend_agent)
    graph.add_node("database_agent", database_agent)
    graph.add_node("devops_agent", devops_agent)
    graph.add_node("integration_agent", integration_agent)
    graph.add_node("qa_agent", qa_agent)
    graph.add_node("increment_iteration", _increment_iteration)

    # Edges: supervisor → workers (sequential, agents self-skip)
    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "frontend_agent")
    graph.add_edge("frontend_agent", "backend_agent")
    graph.add_edge("backend_agent", "database_agent")
    graph.add_edge("database_agent", "devops_agent")

    # Workers → Integration → QA
    graph.add_edge("devops_agent", "integration_agent")
    graph.add_edge("integration_agent", "qa_agent")

    # QA → conditional: end or retry
    graph.add_conditional_edges(
        "qa_agent",
        _route_after_qa,
        {
            "end": END,
            "retry": "increment_iteration",
        },
    )

    # Retry loop back to supervisor
    graph.add_edge("increment_iteration", "supervisor")

    return graph.compile()
