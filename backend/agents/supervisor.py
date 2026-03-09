"""Supervisor Agent — decomposes user requests and delegates to worker agents."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.common import get_llm, retry_with_backoff
from agents.schemas import QAVerdict, SupervisorPlan

logger = logging.getLogger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """\
You are the Supervisor Agent — a senior software architect planning a web application.

Analyze the user's request and create a detailed project plan.

AVAILABLE AGENTS:
- **frontend**: Builds a modern React app (Vite + TypeScript + Tailwind + current ecosystem libs). \
    Use component-driven architecture and production-grade structure.
- **backend**: Builds Python server code (Flask + flask-cors). Entry point is app.py, \
    binds to 0.0.0.0:5000. API routes under /api/*.
- **database**: Designs SQLite schemas, writes migration scripts, creates seed data. \
  All in plain SQL files or Python scripts using sqlite3.
- **devops**: Creates Dockerfile, docker-compose.yml, .env.example, deployment configs.

AGENT SELECTION RULES — BE GENEROUS, when in doubt include the agent:

**ALWAYS assign "frontend"** — every project needs a UI.

**Assign "backend" when ANY of these apply:**
- User mentions: API, server, backend, authentication, login, signup, users, accounts
- User mentions: database, store data, save, persist, CRUD, create/read/update/delete
- User mentions: real-time, WebSocket, notifications, email, payments
- User mentions: AI images, Gemini, image generation, text-to-image
- User mentions: dashboard, admin panel, user management
- User mentions: any dynamic functionality beyond a static page
- The app needs to process data, not just display it
- There are multiple pages with different content based on state/user

**Assign "database" when ANY of these apply:**
- User mentions: users, accounts, authentication, profiles
- User mentions: storing, saving, database, data, records, entries
- User mentions: products, orders, inventory, posts, comments, messages
- The backend agent is assigned AND the app manages any kind of data
- There are lists of items that should persist

**Assign "devops" when:**
- Both frontend AND backend agents are assigned
- User explicitly mentions Docker, deployment, hosting
- The project has multiple services that need to be connected

IMPORTANT EXAMPLES:
- "build a todo app" → frontend + backend + database (todos need to be stored!)
- "build a chat app" → frontend + backend + database (messages need to be stored!)
- "build a dashboard" → frontend + backend + database (dashboard data comes from somewhere!)
- "build a landing page" or "build a portfolio" → frontend only
- "build a calculator" or "build a game" → frontend only (client-side logic)

When in doubt between "frontend only" and "frontend + backend + database", \
CHOOSE the fuller option. Users expect working apps, not static mockups.

SHARED CONTEXT — you MUST provide:
- api_base: the base URL for API calls (usually "/api")
- port: the main user-facing port (always 3000 for sandbox preview)
- backend_port: API server port (5000)
- project_structure: brief description of file organization
- frontend_stack: preferred frontend stack (react_vite_ts_tailwind)
- ui_libraries: comma-separated list of modern libs (zustand, react-router-dom, \
    @tanstack/react-query, chart.js/recharts, framer-motion, lucide-react, \
    react-hook-form, zod)
- needs_gemini_images: true/false

OUTPUT FORMAT: Return a structured SupervisorPlan JSON object.
Provide DETAILED instructions to each agent — don't be vague.
"""

SUPERVISOR_RETRY_PROMPT = """\
The previous attempt FAILED. Here is the QA feedback:

## Issues
{issues}

## Failing Agent
{failing_agent}

## Terminal Output
```
{terminal_output}
```

## Fix Instructions
{fix_instructions}

Revise the project plan. Focus the failing agent's task on fixing these specific \
issues. Keep other agents' tasks minimal (they can reuse their previous output \
if their code was fine).
"""


@retry_with_backoff(max_retries=2)
def _call_supervisor_llm(messages: list) -> SupervisorPlan:
    """Make the structured LLM call for the supervisor."""
    llm = get_llm(temperature=0.2, agent_name="supervisor")
    structured_llm = llm.with_structured_output(SupervisorPlan)
    result = structured_llm.invoke(messages)
    if result is None:
        raise RuntimeError("Supervisor returned None — retrying.")
    return result


def supervisor(state: dict) -> dict:
    """Supervisor node: analyse prompt, create plan, assign agents."""
    iteration = state.get("iteration", 0)
    qa_verdict_raw = state.get("qa_verdict")

    messages_for_llm = [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)]

    # Add the original user prompt
    for msg in state.get("messages", []):
        messages_for_llm.append(msg)

    # On retry iterations, include QA feedback
    if iteration > 0 and qa_verdict_raw:
        verdict = QAVerdict(**qa_verdict_raw) if isinstance(qa_verdict_raw, dict) else qa_verdict_raw
        retry_context = SUPERVISOR_RETRY_PROMPT.format(
            issues="\n".join(f"- {i}" for i in verdict.issues) if verdict.issues else "None specified",
            failing_agent=verdict.failing_agent or "unknown",
            terminal_output=state.get("terminal_output", "(no output)"),
            fix_instructions=verdict.fix_instructions or "No specific instructions.",
        )
        messages_for_llm.append(HumanMessage(content=retry_context))

    try:
        plan = _call_supervisor_llm(messages_for_llm)
    except Exception as exc:
        logger.error("Supervisor failed: %s", exc)
        # Fallback: frontend-only plan
        plan = SupervisorPlan(
            project_name="project",
            stack={"frontend": "react_vite_ts_tailwind"},
            agents_needed=["frontend"],
            shared_context={"api_base": "/api", "port": 3000},
            tasks=[{
                "agent": "frontend",
                "instructions": "Build a complete React app using Vite + TypeScript + Tailwind and modern UI libraries.",
            }],
        )

    plan_summary = (
        f"Project: {plan.project_name}\n"
        f"Stack: {plan.stack}\n"
        f"Agents: {', '.join(plan.agents_needed)}\n"
        f"Tasks: {len(plan.tasks)}"
    )

    return {
        "messages": [AIMessage(content=f"[Supervisor] {plan_summary}")],
        "current_task": "delegating",
        "plan": plan_summary,
        "supervisor_plan": plan.model_dump(),
        "agents_needed": plan.agents_needed,
    }
