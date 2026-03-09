"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";

const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });
import {
  ArrowLeft,
  Rocket,
  Sparkles,
  ExternalLink,
  Copy,
  Check,
  Loader2,
  Code2,
  Zap,
  Monitor,
  Upload,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BedrockModel {
  key: string;
  name: string;
  provider: string;
  tier: string;
  color: string;
  description: string;
}

interface GenerateResult {
  html: string;
  html_length: number;
  model_used: string;
}

// ---------------------------------------------------------------------------
// API Base URL
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Build & Host Page
// ---------------------------------------------------------------------------

export default function BuildPage() {
  const [models, setModels] = useState<BedrockModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("amazon-nova-pro");
  const [prompt, setPrompt] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isDeploying, setIsDeploying] = useState<boolean>(false);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [deployUrl, setDeployUrl] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");
  const [codeCopied, setCodeCopied] = useState<boolean>(false);
  const [urlCopied, setUrlCopied] = useState<boolean>(false);

  // Fetch available models on mount
  useEffect(() => {
    async function fetchModels() {
      try {
        const res = await fetch(`${API_BASE}/api/bedrock-models`);
        if (res.ok) {
          const data = await res.json();
          setModels(data);
        }
      } catch (err) {
        console.error("Failed to fetch models:", err);
      }
    }
    fetchModels();
  }, []);

  // Step 1: Generate HTML only
  async function handleGenerate() {
    if (!prompt.trim()) {
      setError("Please enter a prompt describing your website.");
      return;
    }
    setIsGenerating(true);
    setError(null);
    setResult(null);
    setDeployUrl("");

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim(), model: selectedModel }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Generation failed");
      setResult(data);
      setActiveTab("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsGenerating(false);
    }
  }

  // Step 2: Deploy to Vercel
  async function handleDeploy() {
    if (!result?.html) return;
    setIsDeploying(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/deploy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ html: result.html, prompt: prompt.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Deployment failed");
      setDeployUrl(data.deploy_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deployment failed");
    } finally {
      setIsDeploying(false);
    }
  }

  // Copy HTML code
  function handleCopyCode() {
    if (result?.html) {
      navigator.clipboard.writeText(result.html);
      setCodeCopied(true);
      setTimeout(() => setCodeCopied(false), 2000);
    }
  }

  // Open preview in new browser tab
  function handleOpenInNewTab() {
    if (!result?.html) return;
    const blob = new Blob([result.html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    // Revoke after a short delay to free memory
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }

  // Copy deploy URL
  function handleCopyUrl() {
    if (deployUrl) {
      navigator.clipboard.writeText(deployUrl);
      setUrlCopied(true);
      setTimeout(() => setUrlCopied(false), 2000);
    }
  }

  // Get tier color
  function getTierColor(tier: string): string {
    switch (tier) {
      case "flagship":
        return "text-violet-400 bg-violet-500/10 border-violet-500/20";
      case "premium":
        return "text-blue-400 bg-blue-500/10 border-blue-500/20";
      case "standard":
        return "text-orange-400 bg-orange-500/10 border-orange-500/20";
      case "value":
        return "text-cyan-400 bg-cyan-500/10 border-cyan-500/20";
      case "budget":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      default:
        return "text-zinc-400 bg-zinc-500/10 border-zinc-500/20";
    }
  }

  return (
    <div className="min-h-screen bg-[#030712] text-white">
      {/* Ambient background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_20%_40%,rgba(16,185,129,0.08)_0%,transparent_70%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_50%_60%_at_75%_20%,rgba(139,92,246,0.06)_0%,transparent_70%)]" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-white/[0.05] bg-black/20 backdrop-blur-xl">
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="text-sm">Back to Home</span>
          </Link>
          <div className="flex items-center gap-2">
            <Rocket className="h-5 w-5 text-emerald-400" />
            <span className="font-semibold">Build & Host</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 mx-auto max-w-5xl px-6 py-12">
        {/* Title */}
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3">
            Single-Agent{" "}
            <span className="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
              Website Generator
            </span>
          </h1>
          <p className="text-zinc-400 max-w-xl mx-auto">
            Describe your website in plain English. Our AI will generate a beautiful,
            production-ready React website and deploy it instantly.
          </p>
        </div>

        {/* Model Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-zinc-300 mb-2">
            <Zap className="h-4 w-4 inline mr-1.5 text-amber-400" />
            Select AI Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full bg-[#111113] border border-white/[0.08] rounded-xl px-4 py-3 text-white text-sm focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 outline-none transition-all cursor-pointer"
          >
            {models.map((model) => (
              <option key={model.key} value={model.key}>
                {model.name} ({model.provider}) — {model.description}
              </option>
            ))}
          </select>
          {models.length > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <span
                className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full border ${getTierColor(
                  models.find((m) => m.key === selectedModel)?.tier || ""
                )}`}
              >
                {models.find((m) => m.key === selectedModel)?.tier}
              </span>
              <span className="text-xs text-zinc-500">
                {models.find((m) => m.key === selectedModel)?.provider}
              </span>
            </div>
          )}
        </div>

        {/* Prompt Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-zinc-300 mb-2">
            <Sparkles className="h-4 w-4 inline mr-1.5 text-violet-400" />
            Describe Your Website
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: A modern SaaS landing page for a project management tool with a hero section, features grid, pricing table, and contact form. Use a dark theme with blue accents."
            rows={5}
            className="w-full bg-[#111113] border border-white/[0.08] rounded-xl px-4 py-3 text-white text-sm placeholder-zinc-600 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 outline-none transition-all resize-none"
          />
          <p className="mt-2 text-xs text-zinc-500">
            Be specific! Include sections, features, colors, and style preferences.
          </p>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className={`w-full py-4 rounded-xl font-semibold text-white flex items-center justify-center gap-2 transition-all ${
            isGenerating || !prompt.trim()
              ? "bg-zinc-800 cursor-not-allowed"
              : "bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:-translate-y-0.5"
          }`}
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="h-5 w-5" />
              Generate Website
            </>
          )}
        </button>

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Generated Result */}
        {result && (
          <div className="mt-8 rounded-2xl bg-[#111113] border border-white/[0.06] shadow-lg overflow-hidden">

            {/* Result Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-3">
                <div className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                <span className="text-sm font-medium text-emerald-400">Generated Successfully</span>
                <span className="text-xs text-zinc-500">{result.html_length.toLocaleString()} chars · {result.model_used}</span>
              </div>
              {/* Regenerate */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="text-xs text-zinc-400 hover:text-white transition-colors flex items-center gap-1"
              >
                {isGenerating ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                Regenerate
              </button>
            </div>

            {/* Tabs */}
            <div className="flex items-center justify-between border-b border-white/[0.06] px-2">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setActiveTab("preview")}
                  className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "preview"
                      ? "border-emerald-400 text-emerald-400"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Monitor className="h-3.5 w-3.5" />
                  Preview
                </button>
                <button
                  onClick={() => setActiveTab("code")}
                  className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "code"
                      ? "border-blue-400 text-blue-400"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Code2 className="h-3.5 w-3.5" />
                  Code
                </button>
              </div>
              {/* Open in new tab — always visible once result exists */}
              <button
                onClick={handleOpenInNewTab}
                title="Open preview in new tab"
                className="flex items-center gap-1.5 px-3 py-1.5 mr-1 rounded-lg text-xs text-zinc-400 hover:text-white hover:bg-white/[0.07] transition-all"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Open in new tab
              </button>
            </div>

            {/* Preview Tab — local srcdoc, no Vercel needed */}
            {activeTab === "preview" && (
              <div className="bg-white">
                <iframe
                  srcDoc={result.html}
                  className="w-full"
                  style={{ height: "82vh", minHeight: "640px", display: "block" }}
                  title="Generated Website Preview"
                  sandbox="allow-scripts allow-same-origin"
                />
              </div>
            )}

            {/* Code Tab */}
            {activeTab === "code" && (
              <div>
                <div className="flex items-center justify-between px-4 py-2 bg-[#1e1e1e] border-b border-white/[0.06]">
                  <span className="text-xs text-zinc-400 font-mono">index.html</span>
                  <button
                    onClick={handleCopyCode}
                    className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors"
                  >
                    {codeCopied ? (
                      <><Check className="h-3.5 w-3.5 text-emerald-400" /><span className="text-emerald-400">Copied!</span></>
                    ) : (
                      <><Copy className="h-3.5 w-3.5" /><span>Copy</span></>
                    )}
                  </button>
                </div>
                <Editor
                  height="500px"
                  language="html"
                  value={result.html}
                  theme="vs-dark"
                  options={{
                    readOnly: true,
                    minimap: { enabled: true },
                    fontSize: 13,
                    scrollBeyondLastLine: false,
                    wordWrap: "on",
                    lineNumbers: "on",
                    renderLineHighlight: "all",
                    padding: { top: 12 },
                  }}
                />
              </div>
            )}

            {/* Deploy Section */}
            <div className="px-5 py-4 border-t border-white/[0.06] bg-black/20">
              {deployUrl ? (
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs text-emerald-400 font-medium mr-2">Deployed!</span>
                  <input
                    readOnly
                    value={deployUrl}
                    className="flex-1 bg-black/30 border border-white/[0.05] rounded-lg px-3 py-1.5 text-white text-xs font-mono"
                  />
                  <button
                    onClick={handleCopyUrl}
                    className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] transition-colors"
                  >
                    {urlCopied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-zinc-400" />}
                  </button>
                  <a
                    href={deployUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 transition-colors"
                  >
                    <ExternalLink className="h-3.5 w-3.5 text-emerald-400" />
                  </a>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <p className="text-xs text-zinc-500">Happy with the result? Deploy it live to Vercel.</p>
                  <button
                    onClick={handleDeploy}
                    disabled={isDeploying}
                    className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold text-white transition-all ${
                      isDeploying
                        ? "bg-zinc-700 cursor-not-allowed"
                        : "bg-gradient-to-r from-blue-500 to-violet-500 hover:from-blue-400 hover:to-violet-400 shadow-lg shadow-blue-500/20 hover:-translate-y-0.5"
                    }`}
                  >
                    {isDeploying ? (
                      <><Loader2 className="h-4 w-4 animate-spin" />Deploying...</>
                    ) : (
                      <><Upload className="h-4 w-4" />Deploy to Vercel</>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Example Prompts */}
        <div className="mt-12">
          <p className="text-xs text-zinc-500 uppercase tracking-wider font-medium mb-4">
            Example Prompts
          </p>
          <div className="grid gap-3">
            {[
              "A portfolio website for a UI/UX designer with a project gallery, about section, and contact form",
              "A crypto dashboard showing wallet balance, transaction history, and price charts",
              "A restaurant landing page with menu, reservation form, location map, and customer reviews",
              "A fitness app landing page with workout features, pricing plans, and testimonials",
            ].map((example, i) => (
              <button
                key={i}
                onClick={() => setPrompt(example)}
                className="text-left p-3 rounded-lg bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] hover:border-white/[0.1] transition-all text-sm text-zinc-400 hover:text-zinc-300"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/[0.05] py-6 mt-12">
        <div className="mx-auto max-w-5xl px-6 text-center text-xs text-zinc-600">
          Powered by AWS Bedrock • Deployed to Vercel
        </div>
      </footer>
    </div>
  );
}
