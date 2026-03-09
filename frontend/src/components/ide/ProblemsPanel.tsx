"use client";

import { useAgentStore } from "@/store/useAgentStore";
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from "lucide-react";

export function ProblemsPanel() {
  const qaVerdict = useAgentStore((s) => s.qaVerdict);
  const isExecuting = useAgentStore((s) => s.isExecuting);

  if (!qaVerdict) {
    return (
      <div className="flex h-full items-center justify-center bg-[#111113]">
        <div className="text-center">
          <Info className="mx-auto mb-2 h-6 w-6 text-zinc-700" />
          <p className="text-xs text-zinc-600">
            {isExecuting ? "QA agent will report issues here..." : "No issues reported"}
          </p>
        </div>
      </div>
    );
  }

  if (qaVerdict.passed && qaVerdict.issues.length === 0) {
    return (
      <div className="flex h-full items-center justify-center bg-[#111113]">
        <div className="text-center">
          <CheckCircle2 className="mx-auto mb-2 h-8 w-8 text-emerald-500" />
          <p className="text-sm font-medium text-emerald-400">All checks passed</p>
          <p className="mt-1 text-xs text-zinc-500">No errors or warnings found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-[#111113]">
      {/* Summary */}
      <div className="flex items-center gap-3 border-b border-[#1E1E22] px-3 py-2">
        <span className="flex items-center gap-1 text-xs">
          {qaVerdict.passed ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5 text-red-500" />
          )}
          <span className={qaVerdict.passed ? "text-emerald-400" : "text-red-400"}>
            {qaVerdict.passed ? "Passed with warnings" : "Failed"}
          </span>
        </span>
        {qaVerdict.failing_agent && (
          <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-400">
            Fix: {qaVerdict.failing_agent}
          </span>
        )}
      </div>

      {/* Issues list */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {qaVerdict.issues.map((issue, i) => (
          <div
            key={i}
            className="flex items-start gap-2 border-b border-[#1E1E22]/50 px-3 py-2 hover:bg-[#1A1A1F] transition-colors"
          >
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
            <p className="text-xs text-zinc-400 leading-relaxed">{issue}</p>
          </div>
        ))}

        {qaVerdict.fix_instructions && (
          <div className="border-t border-[#1E1E22] px-3 py-2">
            <p className="text-[10px] font-medium uppercase text-zinc-500 mb-1">Fix Instructions</p>
            <p className="text-xs text-zinc-400">{qaVerdict.fix_instructions}</p>
          </div>
        )}
      </div>
    </div>
  );
}
