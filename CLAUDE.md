Project Context: We are building a high-performance, multi-agent coding SaaS. The system is fundamentally distributed. Do NOT build monolithic endpoints.

Architecture Rules:

Frontend: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui.

State Management: Zustand ONLY for complex/real-time state (WebSockets, file trees, agent status). Avoid React Context for rapidly changing data.

Authentication & DB: Supabase (PostgreSQL). JWTs must be passed securely to all backend services.

Orchestrator (Backend): Python FastAPI + LangGraph. The Next.js app DOES NOT run agent logic.

Execution: Code is NEVER executed locally. Assume an E2B (English2Bits) microVM architecture.

Coding Standards:

Strict TypeScript typing for all interfaces. No any types.

Error handling must be explicit. Never silently catch errors.

Assume hostility. Do not trust user inputs or AI-generated outputs.

Do not use mock data unless explicitly told to. Write actual integration code.