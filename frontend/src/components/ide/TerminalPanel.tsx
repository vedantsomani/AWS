"use client";

import { useRef, useEffect } from "react";
import { useAgentStore } from "@/store/useAgentStore";
import { Terminal, Trash2 } from "lucide-react";

export function TerminalPanel() {
  const terminalOutput = useAgentStore((s) => s.terminalOutput);
  const isExecuting = useAgentStore((s) => s.isExecuting);
  const runCommand = useAgentStore((s) => s.runCommand);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [terminalOutput]);

  return (
    <div className="flex h-full flex-col bg-[#0A0A0B]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1E1E22] px-3 py-1.5">
        <div className="flex items-center gap-1.5">
          <Terminal className="h-3.5 w-3.5 text-zinc-500" />
          <span className="text-[10px] text-zinc-500 font-medium uppercase">Terminal</span>
        </div>
        {terminalOutput && (
          <button
            className="rounded p-1 text-zinc-600 hover:text-zinc-400 transition-colors"
            title="Clear terminal"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        )}
      </div>

      {/* Output */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 font-mono text-xs scrollbar-thin"
      >
        {runCommand && (
          <div className="mb-2 text-zinc-500">
            <span className="text-emerald-500">$</span> {runCommand}
          </div>
        )}

        {terminalOutput ? (
          <pre className="whitespace-pre-wrap text-zinc-400 leading-relaxed">
            {terminalOutput}
          </pre>
        ) : isExecuting ? (
          <div className="flex items-center gap-2 text-zinc-600">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-500" />
            Waiting for output...
          </div>
        ) : (
          <p className="text-zinc-700 italic">No output yet</p>
        )}

        {isExecuting && terminalOutput && (
          <div className="mt-2 flex items-center gap-2 text-zinc-600">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
            Running...
          </div>
        )}
      </div>
    </div>
  );
}
