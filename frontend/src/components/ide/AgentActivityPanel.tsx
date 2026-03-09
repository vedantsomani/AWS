"use client";

import { useAgentStore, type AgentStatus } from "@/store/useAgentStore";
import { motion, AnimatePresence } from "framer-motion";
import {
  Monitor,
  Server,
  Database,
  Container,
  GitMerge,
  ShieldCheck,
  Brain,
  Loader2,
  CheckCircle2,
  Circle,
} from "lucide-react";

const AGENT_CONFIG: Record<string, { icon: typeof Monitor; color: string; label: string }> = {
  supervisor: { icon: Brain, color: "#A855F7", label: "Supervisor" },
  frontend_agent: { icon: Monitor, color: "#3B82F6", label: "Frontend Agent" },
  backend_agent: { icon: Server, color: "#22C55E", label: "Backend Agent" },
  database_agent: { icon: Database, color: "#A855F7", label: "Database Agent" },
  devops_agent: { icon: Container, color: "#F59E0B", label: "DevOps Agent" },
  integration_agent: { icon: GitMerge, color: "#06B6D4", label: "Integration Agent" },
  qa_agent: { icon: ShieldCheck, color: "#EF4444", label: "QA Agent" },
};

function AgentCard({ agent }: { agent: AgentStatus }) {
  const config = AGENT_CONFIG[agent.node] || {
    icon: Circle,
    color: "#71717A",
    label: agent.name,
  };
  const Icon = config.icon;

  const statusIcon =
    agent.status === "running" ? (
      <Loader2 className="h-3.5 w-3.5 animate-spin" style={{ color: config.color }} />
    ) : agent.status === "complete" ? (
      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
    ) : (
      <Circle className="h-3.5 w-3.5 text-zinc-600" />
    );

  // Supervisor, integration, and QA don't produce files — that's normal, not "skipped"
  const noFileAgents = ["supervisor", "integration_agent", "qa_agent", "increment_iteration"];
  const isNoFileAgent = noFileAgents.includes(agent.node);

  let statusLabel: string;
  if (agent.status === "running") {
    statusLabel = "Working...";
  } else if (agent.status === "complete") {
    if (agent.filesCount > 0) {
      statusLabel = `${agent.filesCount} file${agent.filesCount === 1 ? "" : "s"}`;
    } else if (isNoFileAgent) {
      statusLabel = "Done";
    } else {
      statusLabel = "Done (skipped)";
    }
  } else if (agent.status === "failed") {
    statusLabel = "Failed";
  } else {
    statusLabel = "Idle";
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className={`flex items-center gap-2.5 rounded-md border px-3 py-2 transition-all ${
        agent.status === "running"
          ? "border-[#2A2A2E] bg-[#1A1A1F]"
          : "border-transparent bg-transparent"
      }`}
      style={
        agent.status === "running"
          ? { boxShadow: `0 0 12px ${config.color}15` }
          : undefined
      }
    >
      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md"
        style={{ backgroundColor: `${config.color}20` }}
      >
        <Icon className="h-3.5 w-3.5" style={{ color: config.color }} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-medium text-zinc-300">{config.label}</span>
          {statusIcon}
        </div>
        <p className="truncate text-[10px] text-zinc-500">{statusLabel}</p>
      </div>
    </motion.div>
  );
}

export function AgentActivityPanel() {
  const agentStatuses = useAgentStore((s) => s.agentStatuses);
  const isExecuting = useAgentStore((s) => s.isExecuting);

  const agents = Object.values(agentStatuses);

  if (!isExecuting && agents.length === 0) {
    return (
      <div className="flex h-full items-center justify-center px-4">
        <p className="text-center text-xs text-zinc-600">
          Agent activity will appear here during generation.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 p-2 overflow-y-auto scrollbar-thin">
      <AnimatePresence mode="popLayout">
        {agents.map((agent) => (
          <AgentCard key={agent.node} agent={agent} />
        ))}
      </AnimatePresence>
    </div>
  );
}
