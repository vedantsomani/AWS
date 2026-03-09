"""Integration Agent — merges outputs from all worker agents, resolves conflicts."""

from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.common import get_llm, retry_with_backoff
from agents.schemas import IntegrationResult, SupervisorPlan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback assets — used when agents fail to produce output
# ---------------------------------------------------------------------------

_PLACEHOLDER_HTML = """\
<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>React App</title>
    </head>
    <body>
        <div id="root"></div>
        <script type="module" src="/src/main.tsx"></script>
    </body>
</html>
"""

_PLACEHOLDER_MAIN_TSX = """\
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
);
"""

_PLACEHOLDER_APP_TSX = """\
export default function App() {
    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950/30 to-slate-950 flex items-center justify-center p-8">
            <div className="glass max-w-xl w-full p-8 text-center">
                <h1 className="text-4xl font-bold tracking-tight text-slate-50 mb-3">
                    Project is starting...
                </h1>
                <p className="text-slate-400 text-lg">
                    Frontend fallback is active. Your app will appear here shortly.
                </p>
            </div>
        </main>
    );
}
"""

_PLACEHOLDER_CSS = """\
@import "tailwindcss";

@theme {
  --color-brand: #6366f1;
  --color-brand-light: #818cf8;
  --color-surface: #0f172a;
  --color-surface-light: #1e293b;
  --font-sans: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
}

@utility glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
}

html { scroll-behavior: smooth; }

body {
  margin: 0;
  min-height: 100vh;
  background: #020617;
  color: #e2e8f0;
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}

#root { min-height: 100vh; }
"""

_PLACEHOLDER_PACKAGE_JSON = """\
{
    "name": "generated-react-app",
    "private": true,
    "version": "0.1.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
    },
    "dependencies": {
        "react": "^19.1.0",
        "react-dom": "^19.1.0"
    },
    "devDependencies": {
        "@tailwindcss/vite": "^4.1.11",
        "@vitejs/plugin-react": "^4.7.0",
        "@types/react": "^19.1.8",
        "@types/react-dom": "^19.1.6",
        "tailwindcss": "^4.1.11",
        "typescript": "^5.8.3",
        "vite": "^7.0.0"
    }
}
"""

_PLACEHOLDER_VITE_CONFIG_TS = """\
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react(), tailwindcss()],
    server: {
        host: '0.0.0.0',
        port: 3000,
        allowedHosts: true,
        proxy: {
            '/api': 'http://127.0.0.1:5000',
        },
    },
})
"""

_PLACEHOLDER_TSCONFIG = """\
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": false,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "allowJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": false
  },
  "include": ["src"]
}
"""

_FALLBACK_START_SH = """\
#!/bin/bash
cd /home/user
pip install flask flask-cors > /dev/null 2>&1
npm install > /dev/null 2>&1
# Seed database if files exist
if [ -f schema.sql ]; then python3 -c "import sqlite3; c=sqlite3.connect('/home/user/data.db'); c.executescript(open('schema.sql').read()); c.close()"; fi
if [ -f seed.py ]; then python3 seed.py; fi
# Start backend on 5000
python3 app.py > /tmp/backend.log 2>&1 &
# Build and serve frontend on 3000 for sandbox preview
npm run build && python3 -m http.server 3000 -d dist
"""


def _ensure_minimal_react_files(merged: list[dict[str, str]]) -> list[dict[str, str]]:
    """Ensure the merged file tree has a minimal runnable React/Vite app."""
    existing = {f.get("path", "") for f in merged}
    additions: list[dict[str, str]] = []
    if "package.json" not in existing:
        additions.append({"path": "package.json", "content": _PLACEHOLDER_PACKAGE_JSON})
    if "index.html" not in existing:
        additions.append({"path": "index.html", "content": _PLACEHOLDER_HTML})
    if "src/main.tsx" not in existing:
        additions.append({"path": "src/main.tsx", "content": _PLACEHOLDER_MAIN_TSX})
    if "src/App.tsx" not in existing:
        additions.append({"path": "src/App.tsx", "content": _PLACEHOLDER_APP_TSX})
    if "src/index.css" not in existing:
        additions.append({"path": "src/index.css", "content": _PLACEHOLDER_CSS})
    if "tsconfig.json" not in existing:
        additions.append({"path": "tsconfig.json", "content": _PLACEHOLDER_TSCONFIG})
    return merged + additions


def _ensure_vite_host_compat(merged: list[dict[str, str]]) -> list[dict[str, str]]:
    """Ensure Vite dev server allows dynamic E2B preview hosts."""
    vite_paths = {
        "vite.config.ts",
        "vite.config.js",
        "vite.config.mts",
        "vite.config.mjs",
    }

    found_vite = False
    for f in merged:
        path = f.get("path", "")
        if path not in vite_paths:
            continue
        found_vite = True
        content = f.get("content", "")
        if "allowedHosts" in content:
            continue

        if "server: {" in content:
            content = content.replace(
                "server: {",
                "server: {\n    allowedHosts: true,",
                1,
            )
        elif "defineConfig({" in content:
            content = content.replace(
                "defineConfig({",
                "defineConfig({\n  server: {\n    host: '0.0.0.0',\n    port: 3000,\n    allowedHosts: true,\n    proxy: {\n      '/api': 'http://127.0.0.1:5000',\n    },\n  },",
                1,
            )
        else:
            content += (
                "\n\n// E2B preview host compatibility\n"
                "export default {\n"
                "  server: {\n"
                "    host: '0.0.0.0',\n"
                "    port: 3000,\n"
                "    allowedHosts: true,\n"
                "  },\n"
                "}\n"
            )
        f["content"] = content

    if not found_vite:
        merged.append({"path": "vite.config.ts", "content": _PLACEHOLDER_VITE_CONFIG_TS})

    return merged


def _ensure_tailwind_vite_setup(merged: list[dict[str, str]]) -> list[dict[str, str]]:
    """Ensure generated React apps always have a working style pipeline."""
    path_to_file = {f.get("path", ""): f for f in merged}

    # 1) Ensure package.json has required style/build deps.
    pkg = path_to_file.get("package.json")
    if pkg:
        try:
            pkg_json = json.loads(pkg.get("content", "{}"))
            dev_deps = pkg_json.setdefault("devDependencies", {})
            dev_deps.setdefault("tailwindcss", "^4.1.11")
            dev_deps.setdefault("@tailwindcss/vite", "^4.1.11")
            dev_deps.setdefault("@vitejs/plugin-react", "^4.7.0")
            pkg["content"] = json.dumps(pkg_json, indent=2) + "\n"
        except Exception:
            # Keep original if JSON is malformed; other guards still help.
            pass

    # 2) Ensure vite config includes tailwind vite plugin.
    vite_paths = ["vite.config.ts", "vite.config.js", "vite.config.mts", "vite.config.mjs"]
    vite_file = None
    for p in vite_paths:
        if p in path_to_file:
            vite_file = path_to_file[p]
            break

    if vite_file is None:
        merged.append({"path": "vite.config.ts", "content": _PLACEHOLDER_VITE_CONFIG_TS})
    else:
        content = vite_file.get("content", "")
        if "@tailwindcss/vite" not in content:
            if "import react from '@vitejs/plugin-react'" in content:
                content = content.replace(
                    "import react from '@vitejs/plugin-react'",
                    "import tailwindcss from '@tailwindcss/vite'\nimport react from '@vitejs/plugin-react'",
                    1,
                )
            elif "import react from \"@vitejs/plugin-react\"" in content:
                content = content.replace(
                    "import react from \"@vitejs/plugin-react\"",
                    "import tailwindcss from '@tailwindcss/vite'\nimport react from \"@vitejs/plugin-react\"",
                    1,
                )

        if "plugins: [react()]" in content:
            content = content.replace("plugins: [react()]", "plugins: [react(), tailwindcss()]", 1)
        elif "plugins:[react()]" in content:
            content = content.replace("plugins:[react()]", "plugins:[react(), tailwindcss()]", 1)
        elif "plugins:" in content and "tailwindcss()" not in content:
            content = content.replace("plugins:", "plugins: [tailwindcss()], // patched\n  // original plugins:", 1)

        vite_file["content"] = content

    # 3) Ensure src/index.css exists and imports tailwind.
    css_path = "src/index.css"
    css_file = path_to_file.get(css_path)
    if css_file is None:
        merged.append({"path": css_path, "content": '@import "tailwindcss";\n'})
    else:
        css_content = css_file.get("content", "")
        # Strip Tailwind v3 directives that break v4 builds
        css_content = re.sub(r'@tailwind\s+(base|components|utilities)\s*;', '', css_content)
        if "tailwindcss" not in css_content:
            css_content = '@import "tailwindcss";\n\n' + css_content
        # Clean up excessive blank lines left by stripping
        css_content = re.sub(r'\n{3,}', '\n\n', css_content).strip() + '\n'
        css_file["content"] = css_content

    # Also sanitize any other CSS files that may have v3 directives
    for f in merged:
        p = f.get("path", "")
        if p.endswith(".css") and p != css_path:
            c = f.get("content", "")
            if "@tailwind" in c:
                c = re.sub(r'@tailwind\s+(base|components|utilities)\s*;', '', c)
                c = re.sub(r'\n{3,}', '\n\n', c).strip() + '\n'
                f["content"] = c

    # 4) Ensure main entry imports src/index.css.
    main_candidates = ["src/main.tsx", "src/main.jsx", "src/main.ts", "src/main.js"]
    for path in main_candidates:
        mf = path_to_file.get(path)
        if mf is None:
            continue
        mc = mf.get("content", "")
        if "./index.css" not in mc and '"./index.css"' not in mc and "'./index.css'" not in mc:
            mf["content"] = "import './index.css';\n" + mc
        break

    return merged


def _strip_tw_v3_config_files(merged: list[dict[str, str]]) -> list[dict[str, str]]:
    """Remove tailwind.config.* and postcss.config.* — Tailwind v4 doesn't use them."""
    v3_files = {
        "tailwind.config.ts", "tailwind.config.js", "tailwind.config.mjs", "tailwind.config.cjs",
        "postcss.config.js", "postcss.config.mjs", "postcss.config.cjs", "postcss.config.ts",
    }
    return [f for f in merged if f.get("path", "") not in v3_files]


INTEGRATION_SYSTEM_PROMPT = """\
You are the Integration Agent — a Senior Full-Stack Engineer who merges code \
from multiple specialist agents into a single working project.

YOUR JOB:
1. Receive files from frontend, backend, database, and devops agents.
2. Merge them into a unified file tree.
3. Fix any cross-references: import paths, API URLs, port numbers, env vars.
4. Ensure the frontend correctly calls the backend API endpoints.
5. Ensure the backend correctly references database files/paths.
6. Add any glue code needed (e.g., a startup script, a proxy config).

## CRITICAL: PORT 3000 IS MANDATORY
The E2B sandbox preview URL is ALWAYS on port 3000. You MUST ensure port 3000 \
is serving content. If nothing listens on port 3000 the preview will show \
"Connection refused" and the project FAILS.

MERGE RULES:
- If only frontend files exist:
    - Keep frontend as React + Vite project files
        - Ensure Vite config has: server.host=0.0.0.0, server.port=3000, server.allowedHosts=true
        - Build and serve static output for maximum reliability in E2B preview:
            run_command = "npm install && npm run build && python3 -m http.server 3000 -d dist"
- If backend exists (with or without frontend):
    - Include a start.sh file for documentation, but DO NOT use it as run_command.
    - run_command MUST use && chained commands so each step has proper timeouts.
    - EXACT run_command format (do not deviate):
        run_command = "pip install -q flask flask-cors && npm install && npm run build && python3 -m http.server 3000 -d dist"
    - The backend Flask server must be started INSIDE the generated start.sh (NOT via run_command).
    - Instead, include a setup step that starts the backend before the final server:
        run_command = "pip install -q flask flask-cors && npm install && python3 app.py > /tmp/backend.log 2>&1 & sleep 1 && npm run build && python3 -m http.server 3000 -d dist"
- If database files exist → add seeding as an early step:
        run_command = "pip install -q flask flask-cors && npm install && python3 seed.py 2>/dev/null; python3 app.py > /tmp/backend.log 2>&1 & sleep 1 && npm run build && python3 -m http.server 3000 -d dist"
- DevOps files are included as-is (not executed in sandbox)

## IMPORTANT: run_command RULES:
- ALWAYS use && chained commands. NEVER use "bash start.sh" as run_command.
- The LAST command must be the server: python3 -m http.server 3000 -d dist
- Backend app.py runs in background with & BEFORE the build step
- npm install and npm run build are separate steps so they get proper timeouts

## start.sh TEMPLATE (included as a convenience file, NOT used as run_command):
```bash
#!/bin/bash
cd /home/user
pip install flask flask-cors > /dev/null 2>&1
npm install > /dev/null 2>&1
# Run database seed if it exists
if [ -f seed.py ]; then python3 seed.py; fi
if [ -f schema.sql ]; then python3 -c "import sqlite3; c=sqlite3.connect('/home/user/data.db'); c.executescript(open('schema.sql').read()); c.close()"; fi
# Start backend on 5000 in background
python3 app.py > /tmp/backend.log 2>&1 &
# Build and serve frontend on 3000
npm run build && python3 -m http.server 3000 -d dist
```

## REACT + BACKEND PATTERN (when both frontend and backend exist):
Make sure frontend:
1. Uses Vite config proxy: /api -> http://127.0.0.1:5000
2. Runs with host 0.0.0.0 and port 3000
3. Uses same-origin fetch('/api/...')
4. Sets server.allowedHosts = true (required for *.e2b.app preview hosts)

Make sure backend:
1. Runs on 0.0.0.0:5000
2. Has CORS enabled
3. Exposes API only under /api/*

CONFLICT RESOLUTION:
- Frontend API calls use same-origin fetch (e.g. fetch('/api/todos'))
- Vite dev server serves frontend on 3000 and proxies /api to backend 5000
- Database path must be consistent (use /home/user/data.db)
- Environment variables must be consistent

FILE PATH RULES:
- All paths are relative to the project root
- Frontend: package.json, index.html, src/*, vite.config.*
- Backend: app.py, requirements.txt
- Database: schema.sql, seed.py
- DevOps: Dockerfile, docker-compose.yml, .env.example
- DO NOT include: tailwind.config.*, postcss.config.* (Tailwind v4 uses @tailwindcss/vite plugin — no config files)

## TAILWIND v4 CSS RULES:
- CSS must use: @import "tailwindcss";
- NEVER use: @tailwind base; @tailwind components; @tailwind utilities; (v3 syntax — breaks build)
- Custom tokens use @theme { --color-brand: #6366f1; } in CSS
- Custom utilities use @utility name { ... } in CSS
- @apply ONLY with standard Tailwind classes (never custom/made-up class names)
- Do NOT generate tailwind.config.ts, tailwind.config.js, or postcss.config.js

OUTPUT: Return an IntegrationResult with the merged files and the correct run_command.
"""


_BACKEND_RUN_CMD = (
    "pip install -q flask flask-cors"
    " && npm install"
    " && python3 app.py > /tmp/backend.log 2>&1 & sleep 1"
    " && npm run build"
    " && python3 -m http.server 3000 -d dist"
)

_FRONTEND_ONLY_RUN_CMD = "npm install && npm run build && python3 -m http.server 3000 -d dist"


def _sanitize_run_command(run_cmd: str, has_backend: bool) -> str:
    """Ensure the run_command is an && chain, never 'bash start.sh'.

    The executor splits on '&&' to run setup steps synchronously with proper
    timeouts.  'bash start.sh' runs the entire script as a single background
    process, which causes npm install to time out and port 3000 to stay closed.
    """
    cmd_lower = run_cmd.strip().lower()
    # Reject any variation of "bash start.sh" or "sh start.sh"
    if "start.sh" in cmd_lower:
        logger.warning("Sanitizing run_command: replaced '%s' with && chain", run_cmd)
        return _BACKEND_RUN_CMD if has_backend else _FRONTEND_ONLY_RUN_CMD
    # Reject commands without && (single commands that aren't a simple server)
    if "&&" not in run_cmd and "npm run dev" in cmd_lower:
        logger.warning("Sanitizing run_command: bare npm run dev replaced with build chain")
        return _FRONTEND_ONLY_RUN_CMD
    return run_cmd


def _build_file_summary(label: str, files: list[dict[str, str]]) -> str:
    """Build a formatted summary of files from one agent."""
    if not files:
        return f"## {label}\n(no files)\n"
    parts = [f"## {label}"]
    for f in files:
        parts.append(f"### {f['path']}\n```\n{f['content']}\n```")
    return "\n\n".join(parts)


@retry_with_backoff(max_retries=2)
def _call_integration_llm(messages: list) -> IntegrationResult:
    llm = get_llm(temperature=0.2, max_tokens=16384, agent_name="integration")
    structured_llm = llm.with_structured_output(IntegrationResult)
    result = structured_llm.invoke(messages)
    if result is None:
        raise RuntimeError("Integration agent returned None.")
    return result


def integration_agent(state: dict) -> dict:
    """Integration Agent node: merge all agent outputs into a unified project."""
    frontend_files = state.get("frontend_files", [])
    backend_files = state.get("backend_files", [])
    database_files = state.get("database_files", [])
    devops_files = state.get("devops_files", [])

    plan_raw = state.get("supervisor_plan", {})
    plan = SupervisorPlan(**plan_raw) if plan_raw else None

    # Fast path: if only frontend files, no integration needed
    has_backend = len(backend_files) > 0
    has_database = len(database_files) > 0
    has_devops = len(devops_files) > 0

    if not has_backend and not has_database and not has_devops:
        # Frontend-only: no integration needed
        merged = frontend_files[:]
        # If frontend failed to generate, provide a minimal React/Vite app
        merged = _ensure_minimal_react_files(merged)
        merged = _ensure_vite_host_compat(merged)
        merged = _ensure_tailwind_vite_setup(merged)
        merged = _strip_tw_v3_config_files(merged)
        return {
            "messages": [AIMessage(content=f"[Integration] Frontend-only project — {len(merged)} file(s), no merge needed.")],
            "current_task": "integration",
            "files": merged,
            "run_command": "npm install && npm run build && python3 -m http.server 3000 -d dist",
        }

    # Multi-agent: need LLM to merge
    context_parts = [
        _build_file_summary("Frontend Agent Output", frontend_files),
        _build_file_summary("Backend Agent Output", backend_files),
        _build_file_summary("Database Agent Output", database_files),
        _build_file_summary("DevOps Agent Output", devops_files),
    ]

    if plan:
        context_parts.insert(0, f"## Project: {plan.project_name}\n## Stack: {plan.stack}\n## Shared Context: {plan.shared_context}")

    messages = [
        SystemMessage(content=INTEGRATION_SYSTEM_PROMPT),
        HumanMessage(content="\n\n".join(context_parts)),
    ]

    try:
        result = _call_integration_llm(messages)
    except Exception as exc:
        logger.error("Integration agent failed: %s — falling back to simple merge", exc)
        # Fallback: naive merge of all files
        merged = frontend_files + backend_files + database_files + devops_files
        merged = _ensure_minimal_react_files(merged)
        merged = _ensure_vite_host_compat(merged)
        merged = _ensure_tailwind_vite_setup(merged)
        merged = _strip_tw_v3_config_files(merged)
        if not has_backend:
            run_cmd = "npm install && npm run build && python3 -m http.server 3000 -d dist"
        else:
            # Ensure start.sh exists in fallback (convenience file only)
            has_start = any(f.get("path") == "start.sh" for f in merged)
            if not has_start:
                merged.append({"path": "start.sh", "content": _FALLBACK_START_SH})
            # Patch app.py to run backend on 5000 when frontend serves on 3000
            for f in merged:
                if f.get("path") == "app.py" and "port=3000" in f.get("content", ""):
                    f["content"] = f["content"].replace("port=3000", "port=5000")
            # Use && chain so executor can handle each step with proper timeouts
            run_cmd = (
                "pip install -q flask flask-cors"
                " && npm install"
                " && python3 app.py > /tmp/backend.log 2>&1 & sleep 1"
                " && npm run build"
                " && python3 -m http.server 3000 -d dist"
            )
        return {
            "messages": [AIMessage(content=f"[Integration] Fallback merge — {len(merged)} files.")],
            "current_task": "integration",
            "files": merged,
            "run_command": run_cmd,
        }

    merged = [{"path": f.path, "content": f.content} for f in result.files]
    merged = _ensure_vite_host_compat(merged)
    merged = _ensure_tailwind_vite_setup(merged)
    merged = _strip_tw_v3_config_files(merged)
    filenames = ", ".join(f.path for f in result.files)

    run_cmd = _sanitize_run_command(result.run_command, has_backend)

    return {
        "messages": [AIMessage(content=f"[Integration] Merged {len(merged)} file(s): {filenames}")],
        "current_task": "integration",
        "files": merged,
        "run_command": run_cmd,
    }
