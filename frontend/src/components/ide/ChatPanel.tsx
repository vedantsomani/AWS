"use client";

import { useRef, useEffect } from "react";
import { useAgentStore } from "@/store/useAgentStore";
import { Square, Sparkles } from "lucide-react";

// ---------------------------------------------------------------------------
// Agent badge colors
// ---------------------------------------------------------------------------

function agentBadge(content: string): { label: string; cls: string } {
  if (content.startsWith("[Supervisor]")) return { label: "Supervisor", cls: "bg-purple-500/20 text-purple-400" };
  if (content.startsWith("[Frontend]")) return { label: "Frontend", cls: "bg-blue-500/20 text-blue-400" };
  if (content.startsWith("[Backend]")) return { label: "Backend", cls: "bg-emerald-500/20 text-emerald-400" };
  if (content.startsWith("[Database]")) return { label: "Database", cls: "bg-purple-500/20 text-purple-400" };
  if (content.startsWith("[DevOps]")) return { label: "DevOps", cls: "bg-amber-500/20 text-amber-400" };
  if (content.startsWith("[Integration]")) return { label: "Integration", cls: "bg-cyan-500/20 text-cyan-400" };
  if (content.startsWith("[QA]")) return { label: "QA", cls: "bg-red-500/20 text-red-400" };
  return { label: "Agent", cls: "bg-zinc-600/20 text-zinc-400" };
}

// ---------------------------------------------------------------------------
// Component — Message log only (input is in PromptBar)
// ---------------------------------------------------------------------------

export function ChatPanel() {
  const scrollRef = useRef<HTMLDivElement>(null);

  const messages = useAgentStore((s) => s.messages);
  const isExecuting = useAgentStore((s) => s.isExecuting);
  const error = useAgentStore((s) => s.error);
  const stopGeneration = useAgentStore((s) => s.stopGeneration);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div className="flex h-full flex-col bg-[#0A0A0B]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1E1E22] px-4 py-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Agent Activity
        </span>
        {isExecuting && (
          <button
            onClick={stopGeneration}
            className="flex items-center gap-1 rounded-md bg-red-500/10 px-2 py-1 text-[10px] font-medium text-red-400 hover:bg-red-500/20 transition-colors"
          >
            <Square className="h-2.5 w-2.5" /> Stop
          </button>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-2 scrollbar-thin">
        {messages.length === 0 && !error && (
          <div className="space-y-4 pt-6">
            <div className="text-center">
              <Sparkles className="mx-auto mb-2 h-8 w-8 text-zinc-600" />
              <p className="text-sm font-medium text-zinc-400">
                Agent messages will appear here
              </p>
              <p className="text-xs text-zinc-600 mt-1">
                Use the prompt bar above to start building
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => {
          if (msg.role === "human") {
            return (
              <div key={i} className="flex justify-end">
                <div className="max-w-[85%] rounded-lg bg-blue-600/20 px-3 py-2">
                  <p className="text-xs leading-relaxed text-blue-200">
                    {msg.content}
                  </p>
                </div>
              </div>
            );
          }

          const badge = agentBadge(msg.content);
          return (
            <div key={i} className="space-y-0.5">
              <span
                className={`inline-block rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase ${badge.cls}`}
              >
                {badge.label}
              </span>
              <p className="whitespace-pre-wrap text-xs leading-relaxed text-zinc-400">
                {msg.content.replace(/^\[[\w\s]+\]\s*/, "")}
              </p>
            </div>
          );
        })}

        {error && (
          <div className="rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2">
            <p className="text-xs text-red-400">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
