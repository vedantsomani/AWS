"use client";

import { useState, useMemo, useCallback } from "react";
import { useAgentStore, type AgentFile } from "@/store/useAgentStore";
import {
  ChevronRight,
  ChevronDown,
  FileCode2,
  FileJson,
  FileText,
  FileType,
  FolderOpen,
  Folder,
} from "lucide-react";

// ---------------------------------------------------------------------------
// File icon mapping
// ---------------------------------------------------------------------------

function fileIcon(name: string) {
  const ext = name.split(".").pop()?.toLowerCase() || "";
  switch (ext) {
    case "html":
      return <FileCode2 className="h-3.5 w-3.5 text-orange-400" />;
    case "css":
      return <FileCode2 className="h-3.5 w-3.5 text-blue-400" />;
    case "js":
    case "jsx":
      return <FileCode2 className="h-3.5 w-3.5 text-yellow-400" />;
    case "ts":
    case "tsx":
      return <FileCode2 className="h-3.5 w-3.5 text-blue-500" />;
    case "py":
      return <FileCode2 className="h-3.5 w-3.5 text-green-400" />;
    case "json":
      return <FileJson className="h-3.5 w-3.5 text-amber-400" />;
    case "md":
      return <FileText className="h-3.5 w-3.5 text-zinc-400" />;
    case "sql":
      return <FileCode2 className="h-3.5 w-3.5 text-purple-400" />;
    case "sh":
      return <FileCode2 className="h-3.5 w-3.5 text-emerald-400" />;
    case "yml":
    case "yaml":
      return <FileCode2 className="h-3.5 w-3.5 text-red-400" />;
    case "env":
      return <FileCode2 className="h-3.5 w-3.5 text-zinc-500" />;
    default:
      return <FileType className="h-3.5 w-3.5 text-zinc-500" />;
  }
}

// ---------------------------------------------------------------------------
// Tree node structure
// ---------------------------------------------------------------------------

interface TreeNode {
  name: string;
  path: string;
  isFolder: boolean;
  children: TreeNode[];
  file?: AgentFile;
}

function buildTree(files: AgentFile[]): TreeNode[] {
  const root: TreeNode = { name: "", path: "", isFolder: true, children: [] };

  for (const file of files) {
    const filePath = file.path || file.filename || "";
    const parts = filePath.split("/").filter(Boolean);
    let current = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      const pathSoFar = parts.slice(0, i + 1).join("/");

      let child = current.children.find((c) => c.name === part);
      if (!child) {
        child = {
          name: part,
          path: pathSoFar,
          isFolder: !isLast,
          children: [],
          file: isLast ? file : undefined,
        };
        current.children.push(child);
      }
      current = child;
    }
  }

  // Sort: folders first, then alphabetically
  const sortNodes = (nodes: TreeNode[]) => {
    nodes.sort((a, b) => {
      if (a.isFolder !== b.isFolder) return a.isFolder ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    nodes.forEach((n) => sortNodes(n.children));
  };
  sortNodes(root.children);

  return root.children;
}

// ---------------------------------------------------------------------------
// Tree node component
// ---------------------------------------------------------------------------

function TreeItem({
  node,
  depth,
  activePath,
  onSelect,
  expanded,
  onToggle,
}: {
  node: TreeNode;
  depth: number;
  activePath: string;
  onSelect: (file: AgentFile) => void;
  expanded: Set<string>;
  onToggle: (path: string) => void;
}) {
  const isOpen = expanded.has(node.path);
  const isActive = !node.isFolder && activePath === node.path;

  return (
    <div>
      <button
        onClick={() => {
          if (node.isFolder) {
            onToggle(node.path);
          } else if (node.file) {
            onSelect(node.file);
          }
        }}
        className={`flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left text-xs transition-colors ${
          isActive
            ? "bg-blue-600/15 text-blue-300"
            : "text-zinc-400 hover:bg-[#1A1A1F] hover:text-zinc-200"
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {node.isFolder ? (
          <>
            {isOpen ? (
              <ChevronDown className="h-3 w-3 shrink-0 text-zinc-500" />
            ) : (
              <ChevronRight className="h-3 w-3 shrink-0 text-zinc-500" />
            )}
            {isOpen ? (
              <FolderOpen className="h-3.5 w-3.5 shrink-0 text-blue-400" />
            ) : (
              <Folder className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
            )}
          </>
        ) : (
          <>
            <span className="w-3 shrink-0" />
            {fileIcon(node.name)}
          </>
        )}
        <span className="truncate">{node.name}</span>
      </button>

      {node.isFolder && isOpen && (
        <div>
          {node.children.map((child) => (
            <TreeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              activePath={activePath}
              onSelect={onSelect}
              expanded={expanded}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// FileTree component
// ---------------------------------------------------------------------------

export function FileTree() {
  const files = useAgentStore((s) => s.files);
  const activeFile = useAgentStore((s) => s.activeFile);
  const setActiveFile = useAgentStore((s) => s.setActiveFile);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const tree = useMemo(() => buildTree(files), [files]);

  // Auto-expand all folders when files change
  useMemo(() => {
    const folders = new Set<string>();
    for (const file of files) {
      const path = file.path || file.filename || "";
      const parts = path.split("/").filter(Boolean);
      for (let i = 1; i < parts.length; i++) {
        folders.add(parts.slice(0, i).join("/"));
      }
    }
    setExpanded(folders);
  }, [files]);

  const handleToggle = useCallback((path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }, []);

  const activePath = activeFile?.path || activeFile?.filename || "";

  return (
    <div className="flex h-full flex-col bg-[#0A0A0B]">
      <div className="flex items-center justify-between border-b border-[#1E1E22] px-4 py-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Files
        </span>
        <span className="text-[10px] text-zinc-600">{files.length}</span>
      </div>
      <div className="flex-1 overflow-y-auto py-1 scrollbar-thin">
        {files.length === 0 ? (
          <p className="px-4 py-6 text-center text-xs text-zinc-600 italic">
            No files generated yet
          </p>
        ) : (
          tree.map((node) => (
            <TreeItem
              key={node.path}
              node={node}
              depth={0}
              activePath={activePath}
              onSelect={setActiveFile}
              expanded={expanded}
              onToggle={handleToggle}
            />
          ))
        )}
      </div>
    </div>
  );
}
