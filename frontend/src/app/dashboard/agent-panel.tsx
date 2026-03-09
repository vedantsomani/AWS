"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAgentStore } from "@/store/useAgentStore";

export function AgentPanel() {
  const [prompt, setPrompt] = useState("");

  const {
    connectAndRun,
    isExecuting,
    currentTask,
    plan,
    terminalOutput,
    executionSuccess,
    messages,
    files,
    error,
  } = useAgentStore();

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed || isExecuting) return;
    connectAndRun(trimmed);
  };

  return (
    <div className="space-y-4">
      {/* Prompt input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          type="text"
          placeholder="Describe what you want to build..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={isExecuting}
          className="flex-1"
        />
        <Button type="submit" disabled={isExecuting || prompt.trim().length === 0}>
          {isExecuting ? "Running…" : "Run Agent"}
        </Button>
      </form>

      {/* Status */}
      {(currentTask || error) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {currentTask && (
              <p>
                <span className="text-muted-foreground">Current task:</span>{" "}
                <span className="font-mono">{currentTask}</span>
              </p>
            )}
            {isExecuting && (
              <p className="text-blue-500">Pipeline is executing…</p>
            )}
            {!isExecuting && currentTask === "done" && (
              <p className={executionSuccess ? "text-green-600" : "text-red-500"}>
                {executionSuccess ? "Execution succeeded" : "Execution failed"}
              </p>
            )}
            {error && <p className="text-red-500">Error: {error}</p>}
          </CardContent>
        </Card>
      )}

      {/* Plan */}
      {plan && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-xs text-muted-foreground">
              {plan}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Messages stream */}
      {messages.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Messages</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {messages.map((msg, i) => (
              <div key={i} className="text-xs">
                <span className="font-mono font-semibold text-muted-foreground">
                  [{msg.role}]
                </span>{" "}
                <span className="whitespace-pre-wrap">{msg.content}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Files */}
      {files.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Generated Files ({files.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {files.map((f, i) => (
              <div key={i}>
                <p className="text-xs font-mono font-semibold">{f.filename}</p>
                <pre className="mt-1 max-h-48 overflow-auto rounded bg-muted p-2 text-xs">
                  {f.content}
                </pre>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Terminal output */}
      {terminalOutput && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Terminal Output</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-48 overflow-auto rounded bg-muted p-2 text-xs whitespace-pre-wrap">
              {terminalOutput}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
