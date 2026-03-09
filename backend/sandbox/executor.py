"""E2B sandbox executor — runs code in an isolated microVM."""

from __future__ import annotations

import logging
import os
import time
from typing import TypedDict

from e2b import Sandbox

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Web-server detection patterns
# ---------------------------------------------------------------------------

WEB_SERVER_PATTERNS: list[str] = [
    "python3 -m http.server",
    "python -m http.server",
    "python3 app.py",
    "python app.py",
    "flask run",
    "uvicorn",
    "gunicorn",
    "npm run dev",
    "npm start",
    "npx vite",
    "npx next dev",
    "npx serve",
    "serve ",
    "bash start.sh",
]

# Max seconds to wait for the port to open after launching the server.
_PORT_POLL_TIMEOUT = 190
_PORT_POLL_INTERVAL = 2


def _is_web_server_command(command: str) -> bool:
    """Return True if *command* contains a long-running web server."""
    cmd = command.strip().lower()
    segments = [s.strip() for s in cmd.replace(";", "&&").split("&&")]
    for seg in segments:
        if any(seg.startswith(pat) or seg == pat.strip() for pat in WEB_SERVER_PATTERNS):
            return True
    return False


def _detect_port(command: str, default: int = 3000) -> int:
    """Extract the port from a command string.

    Handles formats like:
    - ``python3 -m http.server 3000``  (positional)
    - ``npx serve --port 8080``        (flag)
    - ``npm run dev -- --port=5173``   (flag with =)
    """
    parts = command.split()

    # python -m http.server <port> — port is the last positional arg
    if "http.server" in command:
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        return 8000  # Python http.server default

    # Flask/app.py defaults to 5000
    if "app.py" in command or "flask run" in command:
        # Check for --port flag first, then default
        for i, part in enumerate(parts):
            if part in ("--port", "-p") and i + 1 < len(parts):
                try:
                    return int(parts[i + 1])
                except ValueError:
                    pass
        return 5000

    # --port / -p flag
    for i, part in enumerate(parts):
        if part in ("--port", "-p") and i + 1 < len(parts):
            try:
                return int(parts[i + 1])
            except ValueError:
                pass
        if part.startswith("--port="):
            try:
                return int(part.split("=", 1)[1])
            except ValueError:
                pass

    return default


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


class ExecutionResult(TypedDict):
    """Structured result from a sandbox code execution."""

    stdout: str
    stderr: str
    exit_code: int
    preview_url: str


# ---------------------------------------------------------------------------
# Build auto-fix helpers
# ---------------------------------------------------------------------------


def _attempt_build_fix(sandbox: "Sandbox", error_output: str) -> bool:
    """Try to fix common build errors in-place inside the sandbox.

    Returns True if any fixes were applied (caller should retry the build).
    """
    fixed = False

    # Fix 1: Strip Tailwind v3 directives from CSS files (breaks Tailwind v4)
    if "@tailwind" in error_output or "Unknown at rule" in error_output:
        logger.info("Auto-fix: stripping @tailwind v3 directives from CSS files")
        sandbox.commands.run(
            "find /home/user/src -name '*.css' -exec "
            "sed -i '/@tailwind/d' {} +",
            cwd="/home/user",
        )
        # Ensure @import "tailwindcss" exists in index.css
        sandbox.commands.run(
            "grep -q 'tailwindcss' /home/user/src/index.css 2>/dev/null || "
            "sed -i '1i @import \"tailwindcss\";' /home/user/src/index.css",
            cwd="/home/user",
        )
        fixed = True

    # Fix 2: Remove tailwind.config.* and postcss.config.* (not used in v4)
    sandbox.commands.run(
        "rm -f /home/user/tailwind.config.* /home/user/postcss.config.*",
        cwd="/home/user",
    )

    # Fix 3: Ensure tsconfig.json exists with permissive settings
    sandbox.commands.run(
        "test -f /home/user/tsconfig.json || "
        "echo '{\"compilerOptions\":{\"target\":\"ES2020\",\"jsx\":\"react-jsx\",\"module\":\"ESNext\","
        "\"moduleResolution\":\"bundler\",\"allowImportingTsExtensions\":true,\"noEmit\":true,"
        "\"skipLibCheck\":true,\"strict\":false,\"esModuleInterop\":true,\"allowJs\":true},"
        "\"include\":[\"src\"]}' > /home/user/tsconfig.json",
        cwd="/home/user",
    )
    fixed = True

    return fixed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def execute_code(
    files: list[dict[str, str]],
    command: str,
    *,
    sandbox_timeout: int = 900,
) -> ExecutionResult:
    """Execute code in an E2B sandbox.

    If *command* is detected as a web-server the sandbox stays alive and a
    ``preview_url`` is returned.  Otherwise the sandbox is killed after
    execution.
    
    Note: sandbox_timeout is set to 900s (15 min) to keep previews alive longer.
    """
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        raise RuntimeError(
            "E2B_API_KEY environment variable is not set. "
            "Get one at https://e2b.dev/dashboard"
        )

    sandbox: Sandbox | None = None
    is_server = _is_web_server_command(command)

    try:
        # Use a custom template if configured
        template = os.getenv("E2B_TEMPLATE")
        create_kwargs: dict = {"timeout": sandbox_timeout, "api_key": api_key}
        if template:
            create_kwargs["template"] = template

        # Pass API keys into sandbox so generated apps can use them
        sandbox_envs: dict[str, str] = {}
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            sandbox_envs["GEMINI_API_KEY"] = gemini_key
        if sandbox_envs:
            create_kwargs["envs"] = sandbox_envs

        logger.info("Creating E2B sandbox (template=%s, timeout=%d)...", template or "default", sandbox_timeout)
        sandbox = Sandbox(**create_kwargs)
        logger.info("Sandbox created: %s", sandbox.sandbox_id)

        # Also write env vars to .bashrc so nohup'd processes inherit them
        if sandbox_envs:
            export_lines = " && ".join(
                f"echo 'export {k}={v}' >> /home/user/.bashrc" for k, v in sandbox_envs.items()
            )
            sandbox.commands.run(export_lines, cwd="/home/user")

        # ---- Write files ---------------------------------------------------
        for file_entry in files:
            filename = file_entry.get("path", "") or file_entry.get("filename", "")
            content = file_entry.get("content", "")
            if not filename:
                continue

            parent_dir = "/".join(filename.split("/")[:-1])
            if parent_dir:
                sandbox.commands.run(f"mkdir -p /home/user/{parent_dir}")

            sandbox.files.write(f"/home/user/{filename}", content)

        # ---- Web-server path -----------------------------------------------
        if is_server:
            port = _detect_port(command)

            # Safety net: if command is "bash start.sh" (should not happen
            # after integration sanitizer, but just in case), convert it into
            # an && chain using the known reliable pattern.
            cmd_lower = command.strip().lower()
            if "start.sh" in cmd_lower and "&&" not in command:
                logger.warning(
                    "Executor safety net: replacing '%s' with && chain", command
                )
                command = (
                    "pip install -q flask flask-cors 2>/dev/null; true"
                    " && npm install"
                    " && python3 app.py > /tmp/backend.log 2>&1 & sleep 1"
                    " && npm run build"
                    " && python3 -m http.server 3000 -d dist"
                )
                port = 3000

            # Split chained commands: run setup commands first, then server in background
            server_cmd = command
            if "&&" in command:
                parts = [p.strip() for p in command.split("&&")]
                setup_cmds = parts[:-1]
                server_cmd = parts[-1]

                # Run setup commands (pip install, db init, etc.) synchronously
                build_failed = False
                for setup_cmd in setup_cmds:
                    if not setup_cmd:
                        continue
                    # If build already failed and we're falling back to dev server,
                    # skip remaining setup commands (there's nothing after build anyway)
                    if build_failed:
                        continue

                    logger.info("Running setup command: %s", setup_cmd)
                    try:
                        timeout_seconds = 60
                        setup_lower = setup_cmd.lower()
                        if (
                            "npm install" in setup_lower
                            or "pnpm install" in setup_lower
                            or "yarn install" in setup_lower
                            or "pip install" in setup_lower
                            or "npm run build" in setup_lower
                        ):
                            # Dependency installs and builds can take significantly longer in a fresh sandbox.
                            timeout_seconds = 420

                        setup_result = sandbox.commands.run(
                            setup_cmd, cwd="/home/user", timeout=timeout_seconds
                        )
                        if setup_result.exit_code != 0:
                            # If npm run build failed, try auto-fix then fall back to dev server
                            if "npm run build" in setup_cmd:
                                logger.warning("Build failed — attempting auto-fix and retry...")
                                _attempt_build_fix(sandbox, setup_result.stderr + setup_result.stdout)
                                retry = sandbox.commands.run(
                                    setup_cmd, cwd="/home/user", timeout=timeout_seconds
                                )
                                if retry.exit_code == 0:
                                    logger.info("Build succeeded after auto-fix!")
                                    continue

                                # Build still failed — fall back to Vite dev server
                                # Dev server is more forgiving: it shows TS errors as
                                # browser overlays instead of killing the whole build.
                                logger.warning(
                                    "Build failed even after fix — falling back to Vite dev server. "
                                    "stderr: %s", (setup_result.stderr or retry.stderr)[:500]
                                )
                                server_cmd = "npx vite --host 0.0.0.0 --port 3000"
                                port = 3000
                                build_failed = True
                                continue
                            else:
                                # Non-build command failed (e.g. npm install) — real error
                                logger.error(
                                    "Setup command failed (exit %d): %s\nstderr: %s",
                                    setup_result.exit_code, setup_cmd,
                                    setup_result.stderr[:500],
                                )
                                return ExecutionResult(
                                    stdout=setup_result.stdout,
                                    stderr=(
                                        f"Setup command failed: {setup_cmd}\n\n"
                                        f"stdout:\n{setup_result.stdout[:2000]}\n\n"
                                        f"stderr:\n{setup_result.stderr[:4000]}"
                                    ),
                                    exit_code=setup_result.exit_code,
                                    preview_url="",
                                )
                    except Exception as exc:
                        logger.error("Setup command error: %s — %s", setup_cmd, exc)
                        return ExecutionResult(
                            stdout="",
                            stderr=f"Setup command error: {setup_cmd}\n{exc}",
                            exit_code=1,
                            preview_url="",
                        )

            logger.info("Starting server: %s (port %d)", server_cmd, port)
            # Source .bashrc so nohup'd process inherits env vars (e.g. GEMINI_API_KEY)
            wrapped_cmd = f"nohup bash -c 'source /home/user/.bashrc 2>/dev/null; {server_cmd}' > /tmp/server.log 2>&1 &"
            sandbox.commands.run(wrapped_cmd, cwd="/home/user")

            # Poll for the port to be available
            started = False
            deadline = time.monotonic() + _PORT_POLL_TIMEOUT
            while time.monotonic() < deadline:
                time.sleep(_PORT_POLL_INTERVAL)
                check = sandbox.commands.run(
                    f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}/ 2>/dev/null || echo 000",
                    cwd="/home/user",
                )
                code = check.stdout.strip()
                if code and code != "000":
                    started = True
                    break

            host = sandbox.get_host(port)
            preview_url = f"https://{host}"

            if started:
                logger.info("Server ready on port %d → %s", port, preview_url)
                return ExecutionResult(
                    stdout=f"Server running on port {port}",
                    stderr="",
                    exit_code=0,
                    preview_url=preview_url,
                )
            else:
                server_log = ""
                try:
                    log_result = sandbox.commands.run(
                        "tail -n 120 /tmp/server.log 2>/dev/null || true",
                        cwd="/home/user",
                    )
                    server_log = log_result.stdout.strip()
                except Exception:
                    server_log = ""

                logger.warning(
                    "Server did not start on port %d after %ds.",
                    port,
                    _PORT_POLL_TIMEOUT,
                )

                # Last resort: serve a minimal error page so port 3000 is never empty
                logger.info("Last resort: serving fallback error page on port 3000")
                sandbox.commands.run(
                    "mkdir -p /home/user/_fallback && "
                    "echo '<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Build Error</title>"
                    "<style>*{margin:0;padding:0;box-sizing:border-box}body{min-height:100vh;display:grid;"
                    "place-items:center;background:#020617;color:#e2e8f0;font-family:system-ui,sans-serif}"
                    ".c{max-width:36rem;padding:2rem;border-radius:1rem;background:rgba(255,255,255,.05);"
                    "border:1px solid rgba(255,255,255,.1);text-align:center}"
                    "h1{font-size:1.5rem;margin-bottom:.75rem;color:#f87171}"
                    "p{color:#94a3b8;line-height:1.6}"
                    "pre{margin-top:1rem;padding:1rem;border-radius:.5rem;background:rgba(0,0,0,.4);"
                    "text-align:left;font-size:.75rem;overflow-x:auto;color:#fbbf24;max-height:300px;overflow-y:auto}"
                    "</style></head><body><div class=\"c\">"
                    "<h1>Build Failed</h1>"
                    "<p>The generated code had errors that prevented it from starting. "
                    "Check the Terminal tab in the IDE for details.</p>"
                    "<pre>" + (server_log or "(no log output)").replace("'", "&#39;").replace("<", "&lt;")[:2000] + "</pre>"
                    "</div></body></html>' > /home/user/_fallback/index.html",
                    cwd="/home/user",
                )
                sandbox.commands.run(
                    "nohup python3 -m http.server 3000 -d /home/user/_fallback > /dev/null 2>&1 &",
                    cwd="/home/user",
                )
                # Give http.server a moment to bind
                time.sleep(1)

                return ExecutionResult(
                    stdout="",
                    stderr=(
                        f"Server did not start on port {port} after {_PORT_POLL_TIMEOUT}s.\n"
                        f"Command: {server_cmd}\n\n"
                        "Recent /tmp/server.log output:\n"
                        f"{server_log or '(no server log output)'}\n\n"
                        "A fallback error page is now being served on port 3000."
                    ),
                    exit_code=1,
                    preview_url=preview_url,
                )

        # ---- Normal path ---------------------------------------------------
        result = sandbox.commands.run(command, cwd="/home/user")

        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            preview_url="",
        )

    except Exception as exc:
        raise RuntimeError(f"E2B sandbox error: {exc}") from exc

    finally:
        if sandbox is not None and not is_server:
            try:
                sandbox.kill()
            except Exception:
                pass
