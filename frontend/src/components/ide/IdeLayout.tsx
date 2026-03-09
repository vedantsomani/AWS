"use client";

import { useState, useEffect } from "react";
import {
  Panel,
  Group,
  Separator,
} from "react-resizable-panels";
import { useAgentStore } from "@/store/useAgentStore";
import { PromptBar } from "@/components/ide/PromptBar";
import { ChatPanel } from "@/components/ide/ChatPanel";
import { FileTree } from "@/components/ide/FileTree";
import { EditorPanel } from "@/components/ide/EditorPanel";
import { PreviewPanel } from "@/components/ide/PreviewPanel";
import { TerminalPanel } from "@/components/ide/TerminalPanel";
import { ProblemsPanel } from "@/components/ide/ProblemsPanel";
import { AgentActivityPanel } from "@/components/ide/AgentActivityPanel";
import {
  Monitor,
  Terminal,
  AlertTriangle,
  Activity,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Bottom tab config
// ---------------------------------------------------------------------------

type BottomTab = "preview" | "terminal" | "agents" | "problems";

const BOTTOM_TABS: { key: BottomTab; label: string; icon: typeof Monitor }[] = [
  { key: "preview", label: "Preview", icon: Monitor },
  { key: "terminal", label: "Terminal", icon: Terminal },
  { key: "agents", label: "Agents", icon: Activity },
  { key: "problems", label: "Problems", icon: AlertTriangle },
];

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

export function IdeLayout() {
  const [activeBottomTab, setActiveBottomTab] = useState<BottomTab>("terminal");
  const previewUrl = useAgentStore((s) => s.previewUrl);
  const isExecuting = useAgentStore((s) => s.isExecuting);
  const qaVerdict = useAgentStore((s) => s.qaVerdict);
  const terminalOutput = useAgentStore((s) => s.terminalOutput);
  const executionSuccess = useAgentStore((s) => s.executionSuccess);

  // Auto-switch to preview when URL arrives
  useEffect(() => {
    if (previewUrl) setActiveBottomTab("preview");
  }, [previewUrl]);

  // Auto-switch to agents tab when executing starts
  useEffect(() => {
    if (isExecuting) setActiveBottomTab("agents");
  }, [isExecuting]);

  // Auto-switch to terminal on error so user sees what went wrong
  useEffect(() => {
    if (!isExecuting && terminalOutput && !executionSuccess && !previewUrl) {
      setActiveBottomTab("terminal");
    }
  }, [isExecuting, terminalOutput, executionSuccess, previewUrl]);

  return (
    <div className="flex flex-col h-full">
      {/* Prompt Input — FULL WIDTH */}
      <PromptBar />

      {/* Main IDE area — horizontal split */}
      <div className="flex-1 overflow-hidden flex">
        {/* ===== LEFT SIDEBAR (fixed width, no resizable panel nesting) ===== */}
        <div className="w-[280px] min-w-[220px] flex flex-col border-r border-[#1E1E22] bg-[#0A0A0B] shrink-0">
          {/* Agent Activity */}
          <div className="border-b border-[#1E1E22]">
            <div className="px-3 py-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                Agent Activity
              </span>
            </div>
            <div className="max-h-[260px] overflow-y-auto scrollbar-thin">
              <AgentActivityPanel />
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-hidden border-b border-[#1E1E22]">
            <ChatPanel />
          </div>

          {/* File Tree */}
          <div className="h-[200px] min-h-[120px] overflow-hidden">
            <FileTree />
          </div>
        </div>

        {/* ===== RIGHT MAIN (editor + bottom tabs, resizable vertically) ===== */}
        <div className="flex-1 overflow-hidden">
          <Group orientation="vertical" className="h-full">
            {/* Editor */}
            <Panel id="editor" defaultSize={55} minSize={25}>
              <EditorPanel />
            </Panel>

            <Separator className="h-[3px] bg-[#1E1E22] hover:bg-blue-500/50 transition-colors cursor-row-resize" />

            {/* Bottom Tabs */}
            <Panel id="bottom" defaultSize={45} minSize={15}>
              <div className="flex h-full flex-col bg-[#111113]">
                {/* Tab bar */}
                <div className="flex items-center border-b border-[#1E1E22] bg-[#0A0A0B]">
                  {BOTTOM_TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeBottomTab === tab.key;

                    const showDot =
                      (tab.key === "preview" && previewUrl && !isActive) ||
                      (tab.key === "problems" && qaVerdict && !qaVerdict.passed && !isActive);

                    return (
                      <button
                        key={tab.key}
                        onClick={() => setActiveBottomTab(tab.key)}
                        className={`relative flex items-center gap-1.5 px-3 py-1.5 text-xs transition-colors ${
                          isActive
                            ? "text-zinc-200 border-b-2 border-b-blue-500 bg-[#111113]"
                            : "text-zinc-500 hover:text-zinc-300"
                        }`}
                      >
                        <Icon className="h-3.5 w-3.5" />
                        {tab.label}
                        {showDot && (
                          <span className="absolute -top-0.5 right-1 h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        )}
                      </button>
                    );
                  })}
                </div>

                {/* Tab content */}
                <div className="flex-1 overflow-hidden">
                  {activeBottomTab === "preview" && <PreviewPanel />}
                  {activeBottomTab === "terminal" && <TerminalPanel />}
                  {activeBottomTab === "agents" && <AgentActivityPanel />}
                  {activeBottomTab === "problems" && <ProblemsPanel />}
                </div>
              </div>
            </Panel>
          </Group>
        </div>
      </div>
    </div>
  );
}