"""DevOps Agent — generates Dockerfile, docker-compose, env configs."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.common import get_llm, retry_with_backoff
from agents.schemas import AgentCodebase, QAVerdict, SupervisorPlan

logger = logging.getLogger(__name__)

DEVOPS_SYSTEM_PROMPT = """\
You are the DevOps Agent — a Senior DevOps Engineer.

RULES:
1. Generate deployment configuration files for the project.
2. Required files:
   - Dockerfile: Multi-stage build, Python 3.11-slim base, non-root user.
   - docker-compose.yml: Services for the app, proper networking.
   - .env.example: All required environment variables with descriptions.
3. Use Alpine/slim base images for small container size.
4. Include health checks in docker-compose.
5. Expose the correct ports (3000 for frontend, 5000 for backend).
6. Mount volumes for persistent data (SQLite DB, uploads).
7. Set proper security defaults: non-root user, read-only filesystem where possible.

OUTPUT: Return an AgentCodebase with your config files.
"""


def _get_task_for_agent(plan: SupervisorPlan) -> str:
    for task in plan.tasks:
        if task.agent == "devops":
            return task.instructions
    return "Create Docker deployment configuration."


@retry_with_backoff(max_retries=2)
def _call_devops_llm(messages: list) -> AgentCodebase:
    llm = get_llm(temperature=0.2, max_tokens=32768, agent_name="devops")
    structured_llm = llm.with_structured_output(AgentCodebase)
    result = structured_llm.invoke(messages)
    if result is None:
        raise RuntimeError("DevOps agent returned None.")
    return result


def devops_agent(state: dict) -> dict:
    """DevOps Agent node: generate deployment configs."""
    plan_raw = state.get("supervisor_plan", {})
    plan = SupervisorPlan(**plan_raw) if plan_raw else None

    agents_needed = state.get("agents_needed", [])
    if "devops" not in agents_needed:
        return {
            "messages": [AIMessage(content="[DevOps] Skipped — not needed.")],
            "current_task": "coding_devops",
            "devops_files": [],
        }

    iteration = state.get("iteration", 0)
    qa_verdict_raw = state.get("qa_verdict")

    if iteration > 0 and qa_verdict_raw:
        verdict = QAVerdict(**qa_verdict_raw) if isinstance(qa_verdict_raw, dict) else qa_verdict_raw
        if verdict.failing_agent and verdict.failing_agent != "devops":
            return {
                "messages": [AIMessage(content="[DevOps] No changes needed.")],
                "current_task": "coding_devops",
                "devops_files": state.get("devops_files", []),
            }

        previous_files = state.get("devops_files", [])
        files_summary = "\n\n".join(
            f"--- {f['path']} ---\n{f['content']}" for f in previous_files
        ) if previous_files else "(no previous files)"

        messages = [
            SystemMessage(content=DEVOPS_SYSTEM_PROMPT),
            HumanMessage(content=f"Fix issues:\n{verdict.fix_instructions}\n\nPrevious:\n{files_summary}"),
        ]
    else:
        task = _get_task_for_agent(plan) if plan else "Create deployment configs."
        shared = plan.shared_context if plan else {}
        stack = plan.stack if plan else {}
        context = f"## Task\n{task}\n\n## Stack\n{stack}\n\n## Shared Context\n{shared}"
        messages = [
            SystemMessage(content=DEVOPS_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]

    try:
        result = _call_devops_llm(messages)
    except Exception as exc:
        logger.error("DevOps agent failed: %s", exc)
        return {
            "messages": [AIMessage(content=f"[DevOps] Generation failed: {exc}")],
            "current_task": "coding_devops",
            "devops_files": [],
        }

    files = [{"path": f.path, "content": f.content} for f in result.files]
    filenames = ", ".join(f.path for f in result.files)

    return {
        "messages": [AIMessage(content=f"[DevOps] Generated {len(files)} file(s): {filenames}")],
        "current_task": "coding_devops",
        "devops_files": files,
    }
