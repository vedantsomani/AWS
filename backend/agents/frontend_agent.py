"""Frontend Agent — generates modern React frontend code."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.common import get_llm, retry_with_backoff
from agents.design_standards import DESIGN_QUALITY_PROMPT
from agents.schemas import AgentCodebase, QAVerdict, SupervisorPlan

logger = logging.getLogger(__name__)

FRONTEND_SYSTEM_PROMPT = """\
You are the Frontend Agent — a world-class Frontend Engineer and Product Designer \
who builds premium, award-winning React web applications.

## Quality Bar (NON-NEGOTIABLE):
Every screen you build must feel intentional, polished, and production-ready.
Score yourself on these before returning output:
- Visual quality: 9/10+
- UX clarity and hierarchy: 9/10+
- Code structure: 9/10+
- Responsive + accessible: 9/10+

If any area is below 9/10, improve it before returning.

## Tech Stack (MANDATORY):
- React 19 (latest)
- TypeScript (strict, no `any`)
- Vite 7 (latest)
- **Tailwind CSS v4** (latest — uses `@tailwindcss/vite` plugin, NOT v3 config files)
- Lucide React icons
- Framer Motion for meaningful transitions
- React Router for multi-page apps
- Zustand for shared client state
- Recharts or Chart.js for data/dashboards
- React Hook Form + Zod for forms

## ╔══════════════════════════════════════════════════════════════╗
## ║  TAILWIND CSS v4 — CRITICAL RULES (BUILD WILL FAIL IF WRONG) ║
## ╚══════════════════════════════════════════════════════════════╝
##
## Tailwind v4 is COMPLETELY DIFFERENT from v3. Follow these EXACTLY:
##
## 1. NO tailwind.config.js / tailwind.config.ts — DELETE IT. Config is CSS-only.
## 2. NO postcss.config.js — the @tailwindcss/vite plugin handles everything.
## 3. CSS entry file (src/index.css) MUST start with:
##      @import "tailwindcss";
## 4. NEVER use these v3 directives (they cause build errors):
##      ❌ @tailwind base;
##      ❌ @tailwind components;
##      ❌ @tailwind utilities;
## 5. @apply ONLY with standard Tailwind utility classes:
##      ✅ @apply flex items-center gap-4;
##      ❌ @apply bg-background text-text-primary;  (custom tokens don't exist)
## 6. For custom design tokens, use @theme in CSS:
##      @theme {
##        --color-brand: #6366f1;
##        --color-surface: #0f172a;
##        --color-surface-hover: #1e293b;
##        --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
##      }
##    Then use in HTML: class="bg-brand text-surface"
## 7. Custom utilities use @utility:
##      @utility glass {
##        background: rgba(255,255,255,0.05);
##        backdrop-filter: blur(16px);
##        border: 1px solid rgba(255,255,255,0.1);
##      }
##    Then use: class="glass"
## 8. vite.config.ts MUST import and use the Tailwind plugin:
##      import tailwindcss from '@tailwindcss/vite'
##      plugins: [react(), tailwindcss()]
## 9. DO NOT generate tailwind.config.ts or tailwind.config.js files.
##
## If you get this wrong, `npm run build` WILL fail with exit code 1.

## File Structure (MANDATORY):
- package.json
- index.html
- src/main.tsx  (imports ./index.css)
- src/App.tsx
- src/index.css  (starts with @import "tailwindcss";)
- vite.config.ts

Componentized layout for non-trivial apps:
- src/components/*
- src/pages/*
- src/lib/*
- src/hooks/*

## package.json TEMPLATE:
```json
{
  "name": "app",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "lucide-react": "^0.500.0",
    "framer-motion": "^12.12.0"
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
```
Add more deps as needed (react-router-dom, zustand, recharts, zod, etc.).
Do NOT include tailwindcss in "dependencies" — it goes in "devDependencies".

## vite.config.ts TEMPLATE:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: true,
  },
})
```
If a backend API exists, add: `server.proxy: { '/api': 'http://127.0.0.1:5000' }`

## src/index.css TEMPLATE:
```css
@import "tailwindcss";

@theme {
  --color-brand: #6366f1;
  --color-brand-light: #818cf8;
  --color-surface: #0f172a;
  --color-surface-light: #1e293b;
  --color-surface-lighter: #334155;
  --font-sans: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
}

@utility glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
}

@utility gradient-text {
  background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  background: #020617;
  color: #e2e8f0;
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}
```
You SHOULD customize @theme colors and @utility classes to match the app's brand.
NEVER use @tailwind directives. NEVER use @apply with non-existent classes.

## ABSOLUTE RULES:
1. ALWAYS use React + TypeScript + Vite. Never plain HTML/CSS-only.
2. Use Tailwind v4 CSS syntax ONLY (see critical rules above).
3. DO NOT generate tailwind.config.ts or tailwind.config.js — Tailwind v4 doesn't use them.
4. Use `@import "tailwindcss";` — NEVER `@tailwind base/components/utilities;`.
5. Frontend must bind to host 0.0.0.0 port 3000.
6. If backend exists, use same-origin fetch: `fetch('/api/...')`
7. Vite config MUST have: `server.allowedHosts = true`
8. If images needed, integrate with POST /api/images/generate (Gemini-backed).

## DESIGN PHILOSOPHY — Dark, Premium, Polished:
Every app should look like it belongs on Vercel, Linear, or Stripe's product pages.

### Color System:
- Base: slate-950/slate-900 backgrounds, NOT pure black
- Accent: indigo-500/violet-500/purple-500 gradients
- Text: slate-50 for headings, slate-300 for body, slate-500 for muted
- Success: emerald-500, Warning: amber-500, Error: rose-500
- NEVER use default blue-500 buttons on white backgrounds

### Typography:
- Hero headings: text-5xl md:text-7xl font-bold tracking-tight
- Section headings: text-3xl font-semibold tracking-tight
- Body: text-base text-slate-300 leading-relaxed
- Muted: text-sm text-slate-500
- Use gradient text for brand elements: gradient-text custom utility

### Surfaces & Cards:
- Glass cards: glass custom utility + rounded-2xl p-6
- Or: bg-slate-900/80 border border-slate-800 rounded-2xl
- Hover: hover:bg-slate-800/80 hover:border-slate-700 transition-all duration-300
- Shadow: shadow-2xl shadow-black/25

### Buttons:
- Primary: bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white rounded-xl px-6 py-3 font-medium shadow-lg shadow-indigo-500/25 transition-all duration-200
- Secondary: bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-200 rounded-xl px-6 py-3 transition-all duration-200
- Ghost: hover:bg-white/5 text-slate-400 hover:text-slate-200 rounded-lg px-4 py-2 transition-colors

### Navigation:
- Sticky top-0, backdrop-blur-2xl bg-slate-950/80 border-b border-slate-800/50
- Logo: gradient-text font-bold text-xl
- Links: text-slate-400 hover:text-white transition-colors

### Backgrounds:
- Gradient: bg-gradient-to-br from-slate-950 via-indigo-950/30 to-slate-950
- Ambient glow: absolute divs with bg-indigo-500/10 blur-3xl rounded-full
- Grid pattern: bg-[linear-gradient(rgba(99,102,241,.04)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,.04)_1px,transparent_1px)] bg-[size:64px_64px]

### Lists & Tables:
- divide-y divide-slate-800
- Row hover: hover:bg-slate-800/50
- Alternating: even:bg-slate-900/50

### Status & Badges:
- Success: bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full px-3 py-1 text-xs font-medium
- Warning: bg-amber-500/10 text-amber-400 border border-amber-500/20
- Error: bg-rose-500/10 text-rose-400 border border-rose-500/20
- Live dot: h-2 w-2 rounded-full bg-emerald-500 animate-pulse

### Animations:
- Entrance: Use Framer Motion with staggerChildren and fadeIn + slideUp
- Hover: hover:scale-[1.02] hover:-translate-y-0.5 transition-transform duration-200
- Focus: focus-visible:ring-2 focus-visible:ring-indigo-500/50 focus-visible:outline-none
- Loading: animate-pulse for skeletons, animate-spin for spinners

### Forms:
- Inputs: bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder:text-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-colors
- Labels: text-sm font-medium text-slate-300 mb-2
- Validation error: text-sm text-rose-400 mt-1

### Empty States:
- Centered icon (from Lucide) with text-slate-600, large size
- Heading: text-lg font-medium text-slate-400
- Subtext: text-sm text-slate-500
- CTA button below

## Content Rules:
- NEVER use "Lorem ipsum" or "Company Name" — use realistic content
- Show 4-6 sample items in any list/grid
- Include micro-copy: button labels, tooltips, empty states, success messages
- Use real-sounding names, dates, descriptions

## Images & Media:
- For placeholder/sample images, use https://picsum.photos/{width}/{height}?random={n}
  Example: <img src="https://picsum.photos/400/300?random=1" />
- For user avatars: https://i.pravatar.cc/150?img={n} (n=1-70)
- For product images: https://picsum.photos/seed/{product-name}/400/400
- NEVER use broken image URLs, local file paths, or import statements for placeholder images
- NEVER leave <img> src empty or use # as src
- All <img> tags MUST have alt text and loading="lazy"
- For icons, use Lucide React (already in dependencies): import { Icon } from 'lucide-react'
- If the app is an AI image generator, show a textarea for prompt + a generate button
  that POSTs to /api/images/generate and displays the returned image

## React Patterns:
- useState for local state, useEffect for side effects
- Proper component decomposition (not everything in App)
- Conditional rendering: loading → error → empty → data
- Array.map() with stable keys for lists
- Event handlers for interactivity

## Output Constraints:
- 5-12 focused files (not 30 tiny files)
- No huge hardcoded datasets
- Reasonable file sizes — break very large components

## Reject Criteria (must NOT appear in output):
- tailwind.config.ts or tailwind.config.js files
- @tailwind base; @tailwind components; @tailwind utilities; directives
- @apply with custom/non-existent classes (bg-background, text-text-primary, etc.)
- Plain unstyled HTML without Tailwind classes
- Missing responsive behavior
- Missing hover/focus/disabled states
- Default browser look or generic Bootstrap-style layout
- postcss.config.js (not needed with @tailwindcss/vite)

OUTPUT: Return an AgentCodebase with all files and a brief note.
""" + DESIGN_QUALITY_PROMPT

FRONTEND_FIX_PROMPT = """\
Your previous frontend code FAILED during QA. Fix the issues below.

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

Return the ENTIRE corrected codebase — not just changed files. Do NOT repeat \
the same mistake.
"""


def _get_task_for_agent(plan: SupervisorPlan) -> str:
    """Extract the frontend task from the supervisor plan."""
    for task in plan.tasks:
        if task.agent == "frontend":
            return task.instructions
    return "Build a complete, visually stunning website based on the project plan."


@retry_with_backoff(max_retries=2)
def _call_frontend_llm(messages: list) -> AgentCodebase:
    """Make the structured LLM call."""
    llm = get_llm(temperature=0.4, max_tokens=32768, agent_name="frontend")
    structured_llm = llm.with_structured_output(AgentCodebase)
    result = structured_llm.invoke(messages)
    if result is None:
        raise RuntimeError("Frontend agent returned None.")
    return result


def frontend_agent(state: dict) -> dict:
    """Frontend Agent node: generate HTML/CSS/JS files."""
    plan_raw = state.get("supervisor_plan", {})
    plan = SupervisorPlan(**plan_raw) if plan_raw else None

    # Check if this agent is needed
    agents_needed = state.get("agents_needed", ["frontend"])
    if "frontend" not in agents_needed:
        return {
            "messages": [AIMessage(content="[Frontend] Skipped — not needed.")],
            "current_task": "coding_frontend",
            "frontend_files": [],
        }

    # Build prompt
    iteration = state.get("iteration", 0)
    qa_verdict_raw = state.get("qa_verdict")

    if iteration > 0 and qa_verdict_raw:
        verdict = QAVerdict(**qa_verdict_raw) if isinstance(qa_verdict_raw, dict) else qa_verdict_raw
        # Skip if QA says a different agent needs fixing
        if verdict.failing_agent and verdict.failing_agent != "frontend":
            return {
                "messages": [AIMessage(content="[Frontend] No changes needed — issue is in another agent.")],
                "current_task": "coding_frontend",
                "frontend_files": state.get("frontend_files", []),
            }

        previous_files = state.get("frontend_files", [])
        files_summary = "\n\n".join(
            f"--- {f['path']} ---\n{f['content']}" for f in previous_files
        ) if previous_files else "(no previous files)"

        prompt = FRONTEND_FIX_PROMPT.format(
            issues="\n".join(f"- {i}" for i in verdict.issues),
            fix_instructions=verdict.fix_instructions,
            previous_files=files_summary,
            terminal_output=state.get("terminal_output", ""),
        )
        messages = [
            SystemMessage(content=FRONTEND_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    else:
        task = _get_task_for_agent(plan) if plan else "Build a premium website."
        shared = plan.shared_context if plan else {}
        context = f"## Task\n{task}\n\n## Shared Context\n{shared}\n\n## Project\n{plan.project_name if plan else 'project'}"
        messages = [
            SystemMessage(content=FRONTEND_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]

    try:
        result = _call_frontend_llm(messages)
    except Exception as exc:
        logger.error("Frontend agent failed: %s", exc)
        return {
            "messages": [AIMessage(content=f"[Frontend] Generation failed: {exc}")],
            "current_task": "coding_frontend",
            "frontend_files": [],
        }

    files = [{"path": f.path, "content": f.content} for f in result.files]
    filenames = ", ".join(f.path for f in result.files)

    return {
        "messages": [AIMessage(content=f"[Frontend] Generated {len(files)} file(s): {filenames}")],
        "current_task": "coding_frontend",
        "frontend_files": files,
    }
