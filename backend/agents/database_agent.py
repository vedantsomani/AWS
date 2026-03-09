"""Database Agent — generates SQLite schemas, migrations, and seed data."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.common import get_llm, retry_with_backoff
from agents.schemas import AgentCodebase, QAVerdict, SupervisorPlan

logger = logging.getLogger(__name__)

DATABASE_SYSTEM_PROMPT = """\
You are the Database Agent — a Senior Database Engineer specializing in SQLite.

RULES:
1. Use SQLite ONLY. No PostgreSQL, MySQL, or other databases.
2. Create a file "schema.sql" with all CREATE TABLE statements.
3. Create a file "seed.py" that uses Python's sqlite3 module to:
   a. Create the database at /home/user/data.db
   b. Run schema.sql
   c. Insert sample/seed data
4. Use proper data types, constraints, and indices.
5. Include foreign key relationships where appropriate.
6. Add a comment block at the top of schema.sql describing the schema.
7. The seed.py script must be idempotent (use IF NOT EXISTS, INSERT OR IGNORE).

OUTPUT: Return an AgentCodebase with your SQL and Python files.
"""

DATABASE_FIX_PROMPT = """\
Your previous database code FAILED during QA. Fix the issues below.

## Issues
{issues}

## Fix Instructions
{fix_instructions}

## Previous Files
{previous_files}

## Terminal Error
```
{terminal_output}
```

Return the ENTIRE corrected codebase.
"""


def _get_task_for_agent(plan: SupervisorPlan) -> str:
    for task in plan.tasks:
        if task.agent == "database":
            return task.instructions
    return "Design a SQLite database schema for the project."


@retry_with_backoff(max_retries=2)
def _call_database_llm(messages: list) -> AgentCodebase:
    llm = get_llm(temperature=0.1, max_tokens=32768, agent_name="database")
    structured_llm = llm.with_structured_output(AgentCodebase)
    result = structured_llm.invoke(messages)
    if result is None:
        raise RuntimeError("Database agent returned None.")
    return result


def database_agent(state: dict) -> dict:
    """Database Agent node: generate schema + seed scripts."""
    plan_raw = state.get("supervisor_plan", {})
    plan = SupervisorPlan(**plan_raw) if plan_raw else None

    agents_needed = state.get("agents_needed", [])
    if "database" not in agents_needed:
        return {
            "messages": [AIMessage(content="[Database] Skipped — not needed.")],
            "current_task": "coding_database",
            "database_files": [],
        }

    iteration = state.get("iteration", 0)
    qa_verdict_raw = state.get("qa_verdict")

    if iteration > 0 and qa_verdict_raw:
        verdict = QAVerdict(**qa_verdict_raw) if isinstance(qa_verdict_raw, dict) else qa_verdict_raw
        if verdict.failing_agent and verdict.failing_agent != "database":
            return {
                "messages": [AIMessage(content="[Database] No changes needed.")],
                "current_task": "coding_database",
                "database_files": state.get("database_files", []),
            }

        previous_files = state.get("database_files", [])
        files_summary = "\n\n".join(
            f"--- {f['path']} ---\n{f['content']}" for f in previous_files
        ) if previous_files else "(no previous files)"

        messages = [
            SystemMessage(content=DATABASE_SYSTEM_PROMPT),
            HumanMessage(content=DATABASE_FIX_PROMPT.format(
                issues="\n".join(f"- {i}" for i in verdict.issues),
                fix_instructions=verdict.fix_instructions,
                previous_files=files_summary,
                terminal_output=state.get("terminal_output", ""),
            )),
        ]
    else:
        task = _get_task_for_agent(plan) if plan else "Design a database schema."
        shared = plan.shared_context if plan else {}
        context = f"## Task\n{task}\n\n## Shared Context\n{shared}"
        messages = [
            SystemMessage(content=DATABASE_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]

    try:
        result = _call_database_llm(messages)
    except Exception as exc:
        logger.error("Database agent failed: %s", exc)
        return {
            "messages": [AIMessage(content=f"[Database] Generation failed: {exc}")],
            "current_task": "coding_database",
            "database_files": [],
        }

    files = [{"path": f.path, "content": f.content} for f in result.files]
    filenames = ", ".join(f.path for f in result.files)

    return {
        "messages": [AIMessage(content=f"[Database] Generated {len(files)} file(s): {filenames}")],
        "current_task": "coding_database",
        "database_files": files,
    }
