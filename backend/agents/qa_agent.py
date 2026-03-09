"""QA Agent — executes merged project in E2B sandbox and validates results."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.common import get_llm, retry_with_backoff
from agents.schemas import QAVerdict
from sandbox.executor import execute_code

logger = logging.getLogger(__name__)

QA_SYSTEM_PROMPT = """\
You are the QA Agent — a Senior QA Engineer. You have just executed a project \
in a sandbox environment.

Analyse the execution results and produce a structured verdict:
1. Did the project start successfully? (passed: true/false)
2. List any issues found.
3. If failed, which agent should fix it?
   - "frontend" for HTML/CSS/JS issues, missing files, broken layouts
   - "backend" for Python/Flask errors, import failures, API issues
   - "database" for SQL errors, schema issues, seed failures
   - "integration" for cross-reference problems, port mismatches, path issues
   - "devops" for Docker/deployment config issues
4. Provide specific fix instructions.

RULES:
- A server returning ANY HTTP status code (200, 404, 500) counts as "started".
- If stdout says "Server running on port X" → it started successfully.
- Do NOT hallucinate errors that are not in the output.
- An empty stderr with exit_code 0 = success.
- If the only issue is "Server starting" (not confirmed) but no errors → pass it.
"""


@retry_with_backoff(max_retries=2)
def _call_qa_llm(messages: list) -> QAVerdict:
    llm = get_llm(temperature=0.1, max_tokens=32768, agent_name="qa")
    structured_llm = llm.with_structured_output(QAVerdict)
    result = structured_llm.invoke(messages)
    if result is None:
        raise RuntimeError("QA agent returned None.")
    return result


def qa_agent(state: dict) -> dict:
    """QA Agent node: execute project in E2B and validate."""
    files = state.get("files", [])
    run_command = state.get("run_command", "")

    if not files:
        return {
            "messages": [AIMessage(content="[QA] No files to test.")],
            "current_task": "done",
            "terminal_output": "No files generated.",
            "execution_success": False,
            "preview_url": "",
            "qa_verdict": QAVerdict(
                passed=False,
                issues=["No files were generated."],
                failing_agent="frontend",
                fix_instructions="Generate at least an index.html file.",
            ).model_dump(),
        }

    if not run_command:
        run_command = "python3 -m http.server 3000"

    # Normalize file keys: agents use 'path', executor expects 'filename'
    executor_files = []
    for f in files:
        executor_files.append({
            "filename": f.get("path", f.get("filename", "")),
            "content": f.get("content", ""),
        })

    # Execute in sandbox
    try:
        result = execute_code(files=executor_files, command=run_command)
    except Exception as exc:
        logger.error("QA sandbox error: %s", exc)
        error_msg = str(exc)
        return {
            "messages": [AIMessage(content=f"[QA] Sandbox error: {error_msg}")],
            "current_task": "qa",
            "terminal_output": f"SANDBOX ERROR: {error_msg}\n\nThis usually means:\n1. E2B_API_KEY is missing or invalid\n2. E2B service is unavailable\n3. The sandbox template doesn't exist\n\nCheck your .env file and E2B dashboard.",
            "execution_success": False,
            "preview_url": "",
            "qa_verdict": QAVerdict(
                passed=False,
                issues=[f"Sandbox execution failed: {error_msg}"],
                failing_agent="integration",
                fix_instructions="Fix the run_command or file structure so the project can start.",
            ).model_dump(),
        }

    preview_url = result.get("preview_url", "")
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)

    # Hard failure: if executor explicitly says server didn't start, don't
    # let the LLM hallucinate a pass.
    executor_hard_failure = (
        exit_code != 0
        and ("Server did not start" in stderr or "fallback error page" in stderr)
    )

    # LLM review
    files_summary = "\n".join(f"- {f.get('path', f.get('filename', '?'))}" for f in files)
    review_prompt = (
        f"## Files\n{files_summary}\n\n"
        f"## Run Command\n{run_command}\n\n"
        f"## Exit Code\n{exit_code}\n\n"
        f"## stdout\n{stdout}\n\n"
        f"## stderr\n{stderr}\n\n"
        f"## Preview URL\n{preview_url or '(none)'}"
    )

    try:
        verdict = _call_qa_llm([
            SystemMessage(content=QA_SYSTEM_PROMPT),
            HumanMessage(content=review_prompt),
        ])
    except Exception as exc:
        logger.warning("QA LLM review failed: %s — using heuristic", exc)
        # Heuristic fallback — only pass when exit_code is 0
        # (preview_url alone is not enough since the executor always serves
        # a fallback error page on port 3000)
        passed = exit_code == 0 and not executor_hard_failure
        verdict = QAVerdict(
            passed=passed,
            issues=[] if passed else [f"Exit code: {exit_code}. stderr: {stderr[:200]}"],
            failing_agent="" if passed else "integration",
            fix_instructions="" if passed else "Check the execution errors.",
        )

    # Override LLM verdict if executor explicitly reported hard failure
    if executor_hard_failure and verdict.passed:
        logger.warning("Overriding QA PASS → FAIL because executor reported hard failure")
        verdict = QAVerdict(
            passed=False,
            issues=["Server did not start on port 3000 (executor reported failure)"] + (verdict.issues or []),
            failing_agent=verdict.failing_agent or "integration",
            fix_instructions=verdict.fix_instructions or "Fix build errors so the project starts on port 3000.",
        )

    status = "PASSED" if verdict.passed else "FAILED"
    issues_text = "; ".join(verdict.issues) if verdict.issues else "All checks passed."
    # Always include both stdout and stderr so the user can see the full picture
    output_parts = []
    if stdout:
        output_parts.append(stdout)
    if stderr:
        output_parts.append(f"\n--- STDERR ---\n{stderr}")
    output_text = "\n".join(output_parts) if output_parts else "(no output)"

    return {
        "messages": [AIMessage(content=f"[QA] {status}: {issues_text}")],
        "current_task": "done" if verdict.passed else "qa",
        "terminal_output": output_text,
        "execution_success": verdict.passed,
        "preview_url": preview_url,
        "qa_verdict": verdict.model_dump(),
    }
