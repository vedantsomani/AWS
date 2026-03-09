"""Backend Agent — generates Python server code (Flask/FastAPI)."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.common import get_llm, retry_with_backoff
from agents.schemas import AgentCodebase, QAVerdict, SupervisorPlan

logger = logging.getLogger(__name__)

BACKEND_SYSTEM_PROMPT = """\
You are the Backend Agent — a Senior Backend Engineer.

RULES:
1. Use Flask + flask-cors ONLY. Never use SQLAlchemy, SocketIO, Celery, Redis, or any other framework.
2. Entry point MUST be "app.py" in the project root.
3. Bind to 0.0.0.0 port 5000: app.run(host='0.0.0.0', port=5000, debug=False)
    Frontend runs on 3000 and proxies /api to backend 5000.
4. Include CORS: from flask_cors import CORS; CORS(app)
5. All API routes MUST be under /api/*. Example: @app.route('/api/todos', methods=['GET'])
6. For database: use sqlite3 from Python standard library ONLY (import sqlite3). \
   Database path: /home/user/data.db
   Use sqlite3.connect() and cursor.execute() directly. NO ORM.
7. Keep requirements.txt to ONLY: flask and flask-cors (two lines, nothing else)
8. Add GET /api/health → {"status": "ok"}
9. Proper error handling: try/except around all route handlers, return jsonify({"error": str(e)}), 500
10. Include sample data in routes — don't return empty arrays. Pre-seed with 3-5 realistic items.
11. Backend should expose API routes only under /api/* and not depend on frontend build artifacts.
12. If the task mentions Gemini/image generation, add:
    - POST /api/images/generate
    - Read "prompt" from JSON body (required, max 1000 chars, validate!)
    - Use GEMINI_API_KEY from os.environ (it will be set in the sandbox)
    - Call Gemini API via urllib.request:
      ```python
      import urllib.request, json, os, base64
      def generate_image(prompt):
          api_key = os.environ.get('GEMINI_API_KEY', '')
          if not api_key:
              return None, 'GEMINI_API_KEY not set'
          url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}'
          body = json.dumps({
              'contents': [{'parts': [{'text': f'Generate an image: {prompt}'}]}],
              'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']}
          }).encode()
          req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
          resp = urllib.request.urlopen(req, timeout=60)
          data = json.loads(resp.read())
          for part in data.get('candidates', [{}])[0].get('content', {}).get('parts', []):
              if 'inlineData' in part:
                  mime = part['inlineData']['mimeType']
                  b64 = part['inlineData']['data']
                  return f'data:{mime};base64,{b64}', None
          return None, 'No image in response'
      ```
    - Return JSON: {"image_url": "data:image/png;base64,..."} on success
    - Return JSON: {"error": "message"}, 500 on failure
    - Add strict input validation and error handling

FORBIDDEN (will crash in sandbox):
- flask-sqlalchemy, flask-socketio, flask-login, flask-jwt, flask-migrate
- Any package not in stdlib except flask and flask-cors
- Any async code (no async def, no await)

OUTPUT: Return an AgentCodebase with app.py and requirements.txt.
"""

BACKEND_FIX_PROMPT = """\
Your previous backend code FAILED during QA. Fix the issues below.

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

Return the ENTIRE corrected codebase. Do NOT repeat the same mistake.
"""


def _get_task_for_agent(plan: SupervisorPlan) -> str:
    for task in plan.tasks:
        if task.agent == "backend":
            return task.instructions
    return "Build a Python Flask API server."


@retry_with_backoff(max_retries=2)
def _call_backend_llm(messages: list) -> AgentCodebase:
    llm = get_llm(temperature=0.1, max_tokens=32768, agent_name="backend")
    structured_llm = llm.with_structured_output(AgentCodebase)
    result = structured_llm.invoke(messages)
    if result is None:
        raise RuntimeError("Backend agent returned None.")
    return result


def backend_agent(state: dict) -> dict:
    """Backend Agent node: generate Python server files."""
    plan_raw = state.get("supervisor_plan", {})
    plan = SupervisorPlan(**plan_raw) if plan_raw else None

    agents_needed = state.get("agents_needed", [])
    if "backend" not in agents_needed:
        return {
            "messages": [AIMessage(content="[Backend] Skipped — not needed.")],
            "current_task": "coding_backend",
            "backend_files": [],
        }

    iteration = state.get("iteration", 0)
    qa_verdict_raw = state.get("qa_verdict")

    if iteration > 0 and qa_verdict_raw:
        verdict = QAVerdict(**qa_verdict_raw) if isinstance(qa_verdict_raw, dict) else qa_verdict_raw
        if verdict.failing_agent and verdict.failing_agent != "backend":
            return {
                "messages": [AIMessage(content="[Backend] No changes needed.")],
                "current_task": "coding_backend",
                "backend_files": state.get("backend_files", []),
            }

        previous_files = state.get("backend_files", [])
        files_summary = "\n\n".join(
            f"--- {f['path']} ---\n{f['content']}" for f in previous_files
        ) if previous_files else "(no previous files)"

        messages = [
            SystemMessage(content=BACKEND_SYSTEM_PROMPT),
            HumanMessage(content=BACKEND_FIX_PROMPT.format(
                issues="\n".join(f"- {i}" for i in verdict.issues),
                fix_instructions=verdict.fix_instructions,
                previous_files=files_summary,
                terminal_output=state.get("terminal_output", ""),
            )),
        ]
    else:
        task = _get_task_for_agent(plan) if plan else "Build a Flask API server."
        shared = plan.shared_context if plan else {}
        context = f"## Task\n{task}\n\n## Shared Context\n{shared}\n\n## Project\n{plan.project_name if plan else 'project'}"
        messages = [
            SystemMessage(content=BACKEND_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]

    try:
        result = _call_backend_llm(messages)
    except Exception as exc:
        logger.error("Backend agent failed: %s", exc)
        return {
            "messages": [AIMessage(content=f"[Backend] Generation failed: {exc}")],
            "current_task": "coding_backend",
            "backend_files": [],
        }

    files = [{"path": f.path, "content": f.content} for f in result.files]
    filenames = ", ".join(f.path for f in result.files)

    return {
        "messages": [AIMessage(content=f"[Backend] Generated {len(files)} file(s): {filenames}")],
        "current_task": "coding_backend",
        "backend_files": files,
    }
