"use client";

import { create } from "zustand";
import {
  createProjectRecord,
  updateProjectStatus,
} from "@/lib/firebase/firestore";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentMessage {
  role: string;
  content: string;
}

export interface AgentFile {
  path: string;
  content: string;
  /** Legacy compat — some frames use 'filename' instead of 'path' */
  filename?: string;
}

export interface QAVerdict {
  passed: boolean;
  issues: string[];
  failing_agent: string;
  fix_instructions: string;
}

export interface AgentStatus {
  name: string;
  node: string;
  status: "idle" | "running" | "complete" | "failed";
  filesCount: number;
}

// ---------------------------------------------------------------------------
// WebSocket frame types
// ---------------------------------------------------------------------------

interface WsFrame {
  type: "agent_start" | "agent_complete" | "node_update" | "final" | "error";
  node?: string;
  agent?: string;
  state?: Partial<WsNodeState>;
  detail?: string;
  files_count?: number;
  preview_url?: string;
}

interface WsNodeState {
  messages: AgentMessage[];
  current_task: string;
  plan: string;
  agents_needed: string[];
  files: AgentFile[];
  frontend_files: AgentFile[];
  backend_files: AgentFile[];
  database_files: AgentFile[];
  devops_files: AgentFile[];
  run_command: string;
  terminal_output: string;
  execution_success: boolean;
  preview_url: string;
  qa_verdict: QAVerdict | null;
  iteration: number;
}

// ---------------------------------------------------------------------------
// Store shape
// ---------------------------------------------------------------------------

export interface AgentStoreState {
  // Core state
  messages: AgentMessage[];
  files: AgentFile[];
  terminalOutput: string;
  currentTask: string;
  plan: string;
  runCommand: string;
  executionSuccess: boolean;
  isExecuting: boolean;
  socket: WebSocket | null;
  error: string | null;
  previewUrl: string | null;
  activeFile: AgentFile | null;

  // Multi-agent state
  agentsNeeded: string[];
  activeNode: string | null;
  activeAgent: string | null;
  agentStatuses: Record<string, AgentStatus>;
  qaVerdict: QAVerdict | null;
  iteration: number;

  // Project tracking
  currentProjectId: string | null;
  currentUserId: string | null;

  // Actions
  connectAndRun: (prompt: string, userId?: string) => void;
  setActiveFile: (file: AgentFile | null) => void;
  updateFile: (path: string, content: string) => void;
  stopGeneration: () => void;
  reset: () => void;
}

// ---------------------------------------------------------------------------
// Initial values
// ---------------------------------------------------------------------------

const INITIAL_STATE: Omit<AgentStoreState, "connectAndRun" | "setActiveFile" | "updateFile" | "stopGeneration" | "reset"> = {
  messages: [],
  files: [],
  terminalOutput: "",
  currentTask: "",
  plan: "",
  runCommand: "",
  executionSuccess: false,
  isExecuting: false,
  socket: null,
  error: null,
  previewUrl: null,
  activeFile: null,
  agentsNeeded: [],
  activeNode: null,
  activeAgent: null,
  agentStatuses: {},
  qaVerdict: null,
  iteration: 0,
  currentProjectId: null,
  currentUserId: null,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function normalizeFile(f: AgentFile): AgentFile {
  return {
    path: f.path || f.filename || "",
    content: f.content || "",
  };
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

const BACKEND_HOST =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";
const WS_URL =
  BACKEND_HOST.replace(/^http/, "ws").replace(/\/$/, "") + "/ws/agent";

export const useAgentStore = create<AgentStoreState>((set, get) => ({
  ...INITIAL_STATE,

  reset: () => {
    const { socket } = get();
    if (socket && socket.readyState <= WebSocket.OPEN) {
      socket.close();
    }
    set({ ...INITIAL_STATE });
  },

  setActiveFile: (file: AgentFile | null) => {
    set({ activeFile: file });
  },

  updateFile: (path: string, content: string) => {
    set((prev) => {
      const newFiles = prev.files.map((f) =>
        (f.path || f.filename) === path ? { ...f, content } : f
      );
      const newActive =
        prev.activeFile && (prev.activeFile.path || prev.activeFile.filename) === path
          ? { ...prev.activeFile, content }
          : prev.activeFile;
      return { files: newFiles, activeFile: newActive };
    });
  },

  stopGeneration: () => {
    const { socket } = get();
    if (socket && socket.readyState <= WebSocket.OPEN) {
      socket.close();
    }
    set({ isExecuting: false, socket: null });
  },

  connectAndRun: async (prompt: string, userId?: string) => {
    const prev = get().socket;
    if (prev && prev.readyState <= WebSocket.OPEN) {
      prev.close();
    }

    let projectId: string | null = null;

    // Save project to Firestore if user is authenticated
    if (userId) {
      try {
        projectId = await createProjectRecord(userId, prompt);
      } catch (error) {
        console.error("Failed to create project record:", error);
      }
    }

    set({ ...INITIAL_STATE, isExecuting: true, currentProjectId: projectId, currentUserId: userId || null });

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      ws.send(JSON.stringify({ prompt }));
    };

    ws.onmessage = (event: MessageEvent<string>) => {
      let frame: WsFrame;
      try {
        frame = JSON.parse(event.data) as WsFrame;
      } catch {
        return;
      }

      switch (frame.type) {
        case "agent_start": {
          const agentName = frame.agent || frame.node || "Unknown";
          const nodeName = frame.node || "";
          set((prev) => ({
            activeNode: nodeName,
            activeAgent: agentName,
            agentStatuses: {
              ...prev.agentStatuses,
              [nodeName]: {
                name: agentName,
                node: nodeName,
                status: "running",
                filesCount: 0,
              },
            },
          }));
          break;
        }

        case "agent_complete": {
          const nodeName = frame.node || "";
          set((prev) => {
            const updates: Partial<AgentStoreState> = {
              agentStatuses: {
                ...prev.agentStatuses,
                [nodeName]: {
                  ...prev.agentStatuses[nodeName],
                  status: "complete",
                  filesCount: frame.files_count || prev.agentStatuses[nodeName]?.filesCount || 0,
                },
              },
            };

            // Capture preview_url from QA agent_complete
            if (frame.preview_url) {
              updates.previewUrl = frame.preview_url;
            }

            return updates;
          });
          break;
        }

        case "node_update": {
          const s = frame.state;
          if (!s) break;

          set((prev) => {
            const next: Partial<AgentStoreState> = {};

            // Append messages
            if (s.messages && s.messages.length > 0) {
              next.messages = [...prev.messages, ...s.messages];
            }

            // Update merged files (from integration/qa agent)
            if (s.files !== undefined && s.files.length > 0) {
              const normalized = s.files.map(normalizeFile);
              next.files = normalized;
              // Keep active file in sync
              if (normalized.length > 0) {
                const currentPath = prev.activeFile?.path || prev.activeFile?.filename;
                const match = currentPath
                  ? normalized.find((f) => f.path === currentPath)
                  : null;
                next.activeFile = match ?? normalized[0];
              } else {
                next.activeFile = null;
              }
            }

            // Scalar fields
            if (s.current_task !== undefined) next.currentTask = s.current_task;
            if (s.plan !== undefined) next.plan = s.plan;
            if (s.run_command !== undefined) next.runCommand = s.run_command;
            if (s.terminal_output !== undefined) next.terminalOutput = s.terminal_output;
            if (s.execution_success !== undefined) next.executionSuccess = s.execution_success;
            if (s.preview_url !== undefined) {
              next.previewUrl = s.preview_url || null;
            }
            if (s.agents_needed !== undefined) next.agentsNeeded = s.agents_needed;
            if (s.qa_verdict !== undefined && s.qa_verdict !== null) {
              next.qaVerdict = s.qa_verdict;
            }
            if (s.iteration !== undefined) next.iteration = s.iteration;

            // Track active node from frame
            if (frame.node) {
              next.activeNode = frame.node;
              next.activeAgent = frame.agent || frame.node;
            }

            return next;
          });
          break;
        }

        case "final": {
          const finalState = frame.state;
          const { currentProjectId, currentUserId } = get();

          // Update project status in Firestore
          if (currentProjectId && currentUserId) {
            updateProjectStatus(currentUserId, currentProjectId, "completed").catch(
              (err) => console.error("Failed to update project status:", err)
            );
          }

          const updates: Partial<AgentStoreState> = {
            isExecuting: false,
            activeNode: null,
            activeAgent: null,
          };

          if (finalState) {
            // Extract preview_url from the accumulated final state
            if (finalState.preview_url) {
              updates.previewUrl = finalState.preview_url;
            }
            // Extract files if we don't have them yet
            if (finalState.files && finalState.files.length > 0) {
              const normalized = finalState.files.map(normalizeFile);
              updates.files = normalized;
              if (normalized.length > 0 && !get().activeFile) {
                updates.activeFile = normalized[0];
              }
            }
            if (finalState.terminal_output !== undefined) {
              updates.terminalOutput = finalState.terminal_output;
            }
            if (finalState.execution_success !== undefined) {
              updates.executionSuccess = finalState.execution_success;
            }
            if (finalState.run_command !== undefined) {
              updates.runCommand = finalState.run_command;
            }
            if (finalState.qa_verdict !== undefined && finalState.qa_verdict !== null) {
              updates.qaVerdict = finalState.qa_verdict;
            }
          }

          set(updates);
          ws.close();
          break;
        }

        case "error": {
          const { currentProjectId, currentUserId } = get();

          // Update project status as failed in Firestore
          if (currentProjectId && currentUserId) {
            updateProjectStatus(
              currentUserId,
              currentProjectId,
              "failed",
              frame.detail ?? "Unknown server error"
            ).catch((err) => console.error("Failed to update project status:", err));
          }

          set({
            isExecuting: false,
            error: frame.detail ?? "Unknown server error",
            activeNode: null,
            activeAgent: null,
          });
          ws.close();
          break;
        }
      }
    };

    ws.onerror = () => {
      set({
        isExecuting: false,
        error: "WebSocket connection error. Is the backend running?",
        socket: null,
      });
    };

    ws.onclose = () => {
      set((prev) => {
        if (prev.isExecuting) {
          return { isExecuting: false, socket: null };
        }
        return { socket: null };
      });
    };

    set({ socket: ws });
  },
}));
