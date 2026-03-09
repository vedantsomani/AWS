"use client";

import { useCallback, useState } from "react";
import { useAgentStore } from "@/store/useAgentStore";
import {
  RefreshCw,
  ExternalLink,
  Monitor,
  Tablet,
  Smartphone,
  Loader2,
  Wifi,
  WifiOff,
} from "lucide-react";

const VIEWPORT_SIZES = {
  desktop: { width: "100%", label: "Desktop", icon: Monitor },
  tablet: { width: "768px", label: "Tablet", icon: Tablet },
  mobile: { width: "375px", label: "Mobile", icon: Smartphone },
} as const;

type ViewportMode = keyof typeof VIEWPORT_SIZES;

export function PreviewPanel() {
  const previewUrl = useAgentStore((s) => s.previewUrl);
  const isExecuting = useAgentStore((s) => s.isExecuting);
  const [iframeKey, setIframeKey] = useState(0);
  const [viewport, setViewport] = useState<ViewportMode>("desktop");
  const [isLoading, setIsLoading] = useState(false);

  const handleRefresh = useCallback(() => {
    setIsLoading(true);
    setIframeKey((k) => k + 1);
  }, []);

  const handleOpenExternal = useCallback(() => {
    if (previewUrl) window.open(previewUrl, "_blank");
  }, [previewUrl]);

  if (!previewUrl) {
    return (
      <div className="flex h-full items-center justify-center bg-[#111113]">
        <div className="text-center">
          {isExecuting ? (
            <>
              <Loader2 className="mx-auto mb-2 h-8 w-8 animate-spin text-blue-500" />
              <p className="text-xs text-zinc-500">Building your project...</p>
            </>
          ) : (
            <>
              <Monitor className="mx-auto mb-2 h-8 w-8 text-zinc-700" />
              <p className="text-xs text-zinc-600">Preview will appear after build</p>
            </>
          )}
        </div>
      </div>
    );
  }

  const vp = VIEWPORT_SIZES[viewport];

  return (
    <div className="flex h-full flex-col bg-[#111113]">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-[#1E1E22] px-3 py-1.5">
        <div className="flex items-center gap-1">
          {/* Viewport toggles */}
          {(Object.keys(VIEWPORT_SIZES) as ViewportMode[]).map((mode) => {
            const cfg = VIEWPORT_SIZES[mode];
            const Icon = cfg.icon;
            return (
              <button
                key={mode}
                onClick={() => setViewport(mode)}
                className={`rounded p-1 transition-colors ${
                  viewport === mode
                    ? "bg-blue-600/20 text-blue-400"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
                title={cfg.label}
              >
                <Icon className="h-3.5 w-3.5" />
              </button>
            );
          })}
        </div>

        {/* URL bar */}
        <div className="mx-3 flex flex-1 items-center gap-1.5 rounded-md border border-[#1E1E22] bg-[#0A0A0B] px-2 py-1">
          <Wifi className="h-3 w-3 text-emerald-500" />
          <span className="flex-1 truncate text-[10px] text-zinc-500 font-mono">
            {previewUrl}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleRefresh}
            className="rounded p-1 text-zinc-500 hover:text-zinc-300 transition-colors"
            title="Refresh"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={handleOpenExternal}
            className="rounded p-1 text-zinc-500 hover:text-zinc-300 transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Iframe */}
      <div className="flex flex-1 items-start justify-center overflow-hidden bg-[#0A0A0B] p-2">
        <div
          className="h-full overflow-hidden rounded-md border border-[#1E1E22] bg-white transition-all duration-300"
          style={{ width: vp.width, maxWidth: "100%" }}
        >
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-[#111113]">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          )}
          <iframe
            key={iframeKey}
            src={previewUrl}
            className="h-full w-full"
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
            title="Live Preview"
            onLoad={() => setIsLoading(false)}
          />
        </div>
      </div>
    </div>
  );
}
