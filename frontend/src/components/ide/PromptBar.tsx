"use client";

import { useState, useRef } from "react";
import { useAgentStore } from "@/store/useAgentStore";
import { useAuthStore } from "@/store/useAuthStore";
import { Send, Square, Sparkles } from "lucide-react";

const SUGGESTIONS = [
  "Build a SaaS dashboard with auth, charts, and user management",
  "Create a real-time chat app with rooms and typing indicators",
  "Build an e-commerce store with cart, checkout, and product pages",
  "Create a project management tool like a mini Trello board",
] as const;

export function PromptBar() {
  const [prompt, setPrompt] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const connectAndRun = useAgentStore((s) => s.connectAndRun);
  const isExecuting = useAgentStore((s) => s.isExecuting);
  const stopGeneration = useAgentStore((s) => s.stopGeneration);
  const user = useAuthStore((s) => s.user);

  const handleSubmit = () => {
    const trimmed = prompt.trim();
    if (!trimmed || isExecuting) return;
    connectAndRun(trimmed, user?.uid);
    setPrompt("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  };

  return (
    <div className="border-b border-[#1E1E22] bg-[#111113] px-4 py-3">
      {/* Suggestion chips — show only when input is empty and idle */}
      {!prompt && !isExecuting && (
        <div className="flex gap-2 mb-3 overflow-x-auto pb-1 scrollbar-hide">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setPrompt(s)}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full
                         bg-[#1E1E22] text-gray-400 hover:text-white
                         hover:bg-[#2A2A2E] transition-colors border border-[#2A2A2E]
                         hover:border-[#3B82F6]/50"
            >
              <Sparkles className="w-3 h-3 inline mr-1.5 text-[#3B82F6]" />
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="flex items-end gap-3 bg-[#0A0A0B] rounded-lg border border-[#2A2A2E]
                      focus-within:border-[#3B82F6]/50 focus-within:shadow-[0_0_20px_rgba(59,130,246,0.1)]
                      transition-all px-4 py-3">
        <textarea
          ref={textareaRef}
          value={prompt}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to build... (Enter to send, Shift+Enter for newline)"
          disabled={isExecuting}
          rows={1}
          className="flex-1 bg-transparent text-sm text-white placeholder-gray-500
                     outline-none resize-none min-h-[24px] max-h-[150px] leading-relaxed
                     disabled:opacity-50"
        />
        {isExecuting ? (
          <button
            onClick={stopGeneration}
            className="flex-shrink-0 p-2 rounded-lg bg-red-500/20 text-red-400
                       hover:bg-red-500/30 transition-colors"
            title="Stop generation"
          >
            <Square className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!prompt.trim()}
            className="flex-shrink-0 p-2 rounded-lg bg-[#3B82F6] text-white
                       hover:bg-[#2563EB] disabled:opacity-30 disabled:cursor-not-allowed
                       transition-colors"
            title="Generate (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
