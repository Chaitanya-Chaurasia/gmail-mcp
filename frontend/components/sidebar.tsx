"use client";

import * as React from "react";
import { Github, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar({
  uiMode,
  onToggleUiMode,
}: {
  uiMode: boolean;
  onToggleUiMode: (v: boolean) => void;
}) {
  const [open, setOpen] = React.useState(true);

  return (
    <aside
      className={cn(
        "flex h-dvh shrink-0 flex-col border-r border-neutral-200 bg-white",
        "transition-[width] duration-200",
        open ? "w-52" : "w-12"
      )}
    >
      <div className="flex items-center justify-between px-3 py-3">
        {open && <span className="text-sm font-semibold tracking-tight">gmail-mcp</span>}
        <button
          onClick={() => setOpen(!open)}
          aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
          className="rounded p-1 text-neutral-500 hover:bg-neutral-100 hover:text-black"
        >
          {open ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-2">
        <a
          href="https://github.com/Chaitanya-Chaurasia/gmail-mcp"
          target="_blank"
          rel="noreferrer"
          className={cn(
            "flex items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] text-neutral-600",
            "hover:bg-neutral-100 hover:text-black",
            !open && "justify-center"
          )}
        >
          <Github className="h-4 w-4 shrink-0" />
          {open && "github repo"}
        </a>

        <button
          onClick={() => onToggleUiMode(!uiMode)}
          className={cn(
            "flex items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] text-neutral-600",
            "hover:bg-neutral-100 hover:text-black",
            !open && "justify-center"
          )}
        >
          {/* mono toggle pill */}
          <span
            className={cn(
              "relative h-4 w-7 shrink-0 rounded-full border transition-colors",
              uiMode ? "border-black bg-black" : "border-neutral-300 bg-white"
            )}
          >
            <span
              className={cn(
                "absolute top-0.5 h-2.5 w-2.5 rounded-full transition-all",
                uiMode ? "left-3.5 bg-white" : "left-0.5 bg-neutral-400"
              )}
            />
          </span>
          {open && "ui mode"}
        </button>
      </nav>

      {open && (
        <p className="px-3 py-3 text-[10px] leading-4 text-neutral-400">
          {uiMode ? "drag tools onto the canvas, run them directly" : "chat with your inbox"}
        </p>
      )}
    </aside>
  );
}
