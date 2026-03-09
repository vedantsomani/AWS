"use client";

import { useState } from "react";
import { useAgentStore } from "@/store/useAgentStore";
import {
  Code2,
  LogOut,
  Settings,
  CreditCard,
  Download,
} from "lucide-react";

interface TopBarProps {
  userEmail?: string;
  onSignOut?: () => void;
}

const PIPELINE_STAGES = [
  { key: "supervisor", label: "Supervisor" },
  { key: "frontend_agent", label: "Frontend" },
  { key: "backend_agent", label: "Backend" },
  { key: "database_agent", label: "Database" },
  { key: "devops_agent", label: "DevOps" },
  { key: "integration_agent", label: "Integration" },
  { key: "qa_agent", label: "QA" },
] as const;

export function TopBar({ userEmail, onSignOut }: TopBarProps) {
  const [projectName, setProjectName] = useState("Untitled Project");
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const activeNode = useAgentStore((s) => s.activeNode);
  const agentStatuses = useAgentStore((s) => s.agentStatuses);
  const isExecuting = useAgentStore((s) => s.isExecuting);
  const iteration = useAgentStore((s) => s.iteration);
  const files = useAgentStore((s) => s.files);
  const currentTask = useAgentStore((s) => s.currentTask);

  const canDownload = !isExecuting && currentTask === "done" && files.length > 0;

  const handleDownload = async () => {
    if (!canDownload || isDownloading) return;
    setIsDownloading(true);
    try {
      const JSZip = (await import("jszip")).default;
      const zip = new JSZip();

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const rawPath = (file.path || file.filename || `file-${i + 1}.txt`).trim();
        const safePath = rawPath.replace(/^\/+/, "");
        zip.file(safePath || `file-${i + 1}.txt`, file.content || "");
      }

      const blob = await zip.generateAsync({ type: "blob" });
      const baseName = projectName
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9-_]+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "") || "generated-project";

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${baseName}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download generated code", error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="flex h-11 shrink-0 items-center justify-between border-b border-[#1E1E22] bg-[#0A0A0B] px-4">
      {/* Logo + Project Name */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-600">
            <Code2 className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-semibold text-zinc-200">CodeSaaS</span>
        </div>
        <span className="text-zinc-600">/</span>
        <input
          type="text"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="bg-transparent text-sm text-zinc-300 outline-none border-none focus:text-white transition-colors w-40"
          spellCheck={false}
        />
      </div>

      {/* Pipeline Status */}
      <div className="flex items-center gap-1">
        {isExecuting && (
          <>
            {PIPELINE_STAGES.map((stage, i) => {
              const status = agentStatuses[stage.key];
              const isActive = activeNode === stage.key;
              const isComplete = status?.status === "complete";
              const isSkipped = status?.status === "complete" && status?.filesCount === 0;

              let dotClass = "bg-zinc-700";
              if (isActive) dotClass = "bg-blue-500 animate-pulse";
              else if (isComplete && !isSkipped) dotClass = "bg-emerald-500";
              else if (isSkipped) dotClass = "bg-zinc-600";

              return (
                <div key={stage.key} className="flex items-center">
                  {i > 0 && (
                    <div className={`h-px w-3 ${isComplete ? "bg-emerald-500/50" : "bg-zinc-700"}`} />
                  )}
                  <div className="group relative flex items-center">
                    <div className={`h-2 w-2 rounded-full ${dotClass}`} />
                    <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[9px] text-zinc-500 opacity-0 group-hover:opacity-100 transition-opacity">
                      {stage.label}
                    </span>
                  </div>
                </div>
              );
            })}
            {iteration > 0 && (
              <span className="ml-2 rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-medium text-amber-400">
                Retry {iteration}
              </span>
            )}
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleDownload}
          disabled={!canDownload || isDownloading}
          className="inline-flex h-7 items-center gap-1.5 rounded-md border border-zinc-700 bg-zinc-900 px-2.5 text-xs font-medium text-zinc-200 transition-colors hover:border-zinc-600 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-zinc-900/60 disabled:text-zinc-500"
          title={canDownload ? "Download generated code" : "Generate code first"}
        >
          <Download className="h-3.5 w-3.5" />
          {isDownloading ? "Preparing..." : "Download Code"}
        </button>
      </div>

      {/* User */}
      <div className="relative flex items-center gap-3">
        {userEmail && (
          <span className="text-xs text-zinc-500 hidden sm:block">{userEmail}</span>
        )}
        <button
          onClick={() => setShowUserMenu((v) => !v)}
          className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-800 text-xs font-medium text-zinc-300 hover:bg-zinc-700 transition-colors"
        >
          {userEmail ? userEmail[0].toUpperCase() : "U"}
        </button>

        {showUserMenu && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
            <div className="absolute right-0 top-full z-50 mt-1 w-48 rounded-lg border border-[#1E1E22] bg-[#111113] py-1 shadow-lg">
              <button className="flex w-full items-center gap-2 px-3 py-2 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200">
                <Settings className="h-3.5 w-3.5" /> Settings
              </button>
              <button className="flex w-full items-center gap-2 px-3 py-2 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200">
                <CreditCard className="h-3.5 w-3.5" /> Billing
              </button>
              <div className="my-1 border-t border-[#1E1E22]" />
              <button
                onClick={onSignOut}
                className="flex w-full items-center gap-2 px-3 py-2 text-xs text-red-400 hover:bg-zinc-800"
              >
                <LogOut className="h-3.5 w-3.5" /> Sign Out
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
