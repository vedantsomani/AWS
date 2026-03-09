"use client";

import { useAgentStore } from "@/store/useAgentStore";
import { Circle, Loader2, CheckCircle2, XCircle } from "lucide-react";

export function StatusBar() {
  const currentTask = useAgentStore((s) => s.currentTask);
  const isExecuting = useAgentStore((s) => s.isExecuting);
  const files = useAgentStore((s) => s.files);
  const executionSuccess = useAgentStore((s) => s.executionSuccess);
  const previewUrl = useAgentStore((s) => s.previewUrl);
  const activeAgent = useAgentStore((s) => s.activeAgent);
  const iteration = useAgentStore((s) => s.iteration);

  const sandboxStatus = isExecuting
    ? { label: "Sandbox: running", color: "bg-amber-500 animate-pulse" }
    : previewUrl
    ? { label: "Sandbox: live", color: "bg-emerald-500" }
    : executionSuccess === false && !isExecuting && currentTask === "done"
    ? { label: "Sandbox: failed", color: "bg-red-500" }
    : { label: "Sandbox: stopped", color: "bg-zinc-600" };

  return (
    <div className="flex h-6 shrink-0 items-center justify-between border-t border-[#1E1E22] bg-[#0A0A0B] px-3 text-[11px]">
      {/* Left side */}
      <div className="flex items-center gap-3">
        {isExecuting ? (
          <span className="flex items-center gap-1.5 text-blue-400">
            <Loader2 className="h-3 w-3 animate-spin" />
            {activeAgent || currentTask || "Processing..."}
          </span>
        ) : currentTask === "done" ? (
          <span className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="h-3 w-3" />
            {executionSuccess ? "Completed" : "Completed with errors"}
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-zinc-500">
            <Circle className="h-3 w-3" />
            Ready
          </span>
        )}

        {iteration > 0 && (
          <span className="text-amber-400">Iteration {iteration}</span>
        )}
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4 text-zinc-500">
        <span>{files.length} file{files.length !== 1 ? "s" : ""}</span>
        <span className="flex items-center gap-1">
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${sandboxStatus.color}`}
          />
          {sandboxStatus.label}
        </span>
      </div>
    </div>
  );
}
