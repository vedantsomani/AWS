"use client";

import { memo, useMemo, useCallback, useState } from "react";
import Editor from "@monaco-editor/react";
import { useAgentStore } from "@/store/useAgentStore";
import { X, FileCode2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Language detection
// ---------------------------------------------------------------------------

function detectLanguage(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    html: "html",
    css: "css",
    js: "javascript",
    jsx: "javascript",
    ts: "typescript",
    tsx: "typescript",
    py: "python",
    json: "json",
    md: "markdown",
    sql: "sql",
    sh: "shell",
    bash: "shell",
    yml: "yaml",
    yaml: "yaml",
    xml: "xml",
    svg: "xml",
    env: "plaintext",
    txt: "plaintext",
    dockerfile: "dockerfile",
  };
  return map[ext] || "plaintext";
}

// ---------------------------------------------------------------------------
// Monaco Editor wrapper (memoized)
// ---------------------------------------------------------------------------

const MonacoViewer = memo(function MonacoViewer({
  content,
  language,
  onChange,
}: {
  content: string;
  language: string;
  onChange: (value: string | undefined) => void;
}) {
  return (
    <Editor
      height="100%"
      language={language}
      value={content}
      onChange={onChange}
      theme="vs-dark"
      options={{
        readOnly: false,
        minimap: { enabled: true },
        fontSize: 13,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        wordWrap: "on",
        tabSize: 2,
        smoothScrolling: true,
        cursorSmoothCaretAnimation: "on",
        padding: { top: 12 },
        renderLineHighlight: "gutter",
        bracketPairColorization: { enabled: true },
        guides: { bracketPairs: true },
        scrollbar: {
          verticalScrollbarSize: 6,
          horizontalScrollbarSize: 6,
        },
      }}
    />
  );
});

// ---------------------------------------------------------------------------
// Editor Panel
// ---------------------------------------------------------------------------

export function EditorPanel() {
  const activeFile = useAgentStore((s) => s.activeFile);
  const files = useAgentStore((s) => s.files);
  const setActiveFile = useAgentStore((s) => s.setActiveFile);
  const updateFile = useAgentStore((s) => s.updateFile);
  const isExecuting = useAgentStore((s) => s.isExecuting);

  // Track open tabs
  const [openTabs, setOpenTabs] = useState<string[]>([]);

  // Sync tabs with active file
  useMemo(() => {
    if (activeFile) {
      const path = activeFile.path || activeFile.filename || "";
      setOpenTabs((prev) => (prev.includes(path) ? prev : [...prev, path]));
    }
  }, [activeFile]);

  const activePath = activeFile?.path || activeFile?.filename || "";
  const language = useMemo(
    () => detectLanguage(activePath),
    [activePath]
  );

  const handleChange = useCallback(
    (value: string | undefined) => {
      if (value !== undefined && activePath) {
        updateFile(activePath, value);
      }
    },
    [activePath, updateFile]
  );

  const handleCloseTab = useCallback(
    (path: string, e: React.MouseEvent) => {
      e.stopPropagation();
      setOpenTabs((prev) => {
        const next = prev.filter((p) => p !== path);
        // If closing the active tab, switch to the nearest remaining tab
        if (activePath === path && next.length > 0) {
          const idx = prev.indexOf(path);
          const newIdx = Math.min(idx, next.length - 1);
          const newPath = next[newIdx];
          const newFile = files.find(
            (f) => (f.path || f.filename) === newPath
          );
          if (newFile) setActiveFile(newFile);
        } else if (next.length === 0) {
          setActiveFile(null);
        }
        return next;
      });
    },
    [activePath, files, setActiveFile]
  );

  const handleSelectTab = useCallback(
    (path: string) => {
      const file = files.find((f) => (f.path || f.filename) === path);
      if (file) setActiveFile(file);
    },
    [files, setActiveFile]
  );

  if (!activeFile) {
    return (
      <div className="flex h-full items-center justify-center bg-[#111113]">
        <div className="text-center">
          <FileCode2 className="mx-auto mb-2 h-10 w-10 text-zinc-700" />
          <p className="text-xs text-zinc-600">
            {isExecuting ? "Generating code..." : "Select a file to edit"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-[#111113]">
      {/* Tabs */}
      <div className="flex items-center border-b border-[#1E1E22] bg-[#0A0A0B] overflow-x-auto scrollbar-thin">
        {openTabs.map((tabPath) => {
          const isActive = tabPath === activePath;
          const fileName = tabPath.split("/").pop() || tabPath;

          return (
            <button
              key={tabPath}
              onClick={() => handleSelectTab(tabPath)}
              className={`group flex items-center gap-1.5 border-r border-[#1E1E22] px-3 py-1.5 text-xs transition-colors ${
                isActive
                  ? "bg-[#111113] text-zinc-200 border-b-2 border-b-blue-500"
                  : "bg-[#0A0A0B] text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span className="truncate max-w-[120px]">{fileName}</span>
              <span
                onClick={(e) => handleCloseTab(tabPath, e)}
                className="ml-1 rounded p-0.5 opacity-0 group-hover:opacity-100 hover:bg-zinc-700 transition-opacity"
              >
                <X className="h-3 w-3" />
              </span>
            </button>
          );
        })}
        {/* Language badge */}
        <div className="ml-auto flex items-center px-3">
          <span className="text-[10px] text-zinc-600 uppercase">{language}</span>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        <MonacoViewer
          content={activeFile.content}
          language={language}
          onChange={handleChange}
        />
      </div>
    </div>
  );
}
