"use client";

import * as React from "react";
import { ArrowUp, ChevronRight, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

/* ---------------------------------------------------------------- types */

type ToolPart = {
  kind: "tool";
  id: string;
  name: string;
  input: unknown;
  output?: string;
};
type TextPart = { kind: "text" | "thinking"; text: string };
type Part = TextPart | ToolPart;

type Msg = {
  role: "user" | "assistant";
  parts: Part[];
  time: string;
};

type SseEvent =
  | { type: "thinking_delta"; text: string }
  | { type: "text_delta"; text: string }
  | { type: "tool_call"; id: string; name: string; input: unknown }
  | { type: "tool_result"; id: string; name: string; output: string }
  | { type: "done" }
  | { type: "error"; message: string };

const now = () =>
  new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

const textOf = (m: Msg) =>
  m.parts.filter((p): p is TextPart => p.kind === "text").map((p) => p.text).join("");

/* ---------------------------------------------------------- sub-renders */

function ThinkingBlock({ text }: { text: string }) {
  const [open, setOpen] = React.useState(false);
  return (
    <button
      onClick={() => setOpen(!open)}
      className="block w-full text-left my-1 group"
    >
      <span className="flex items-center gap-1 text-[11px] uppercase tracking-wider text-neutral-400">
        <ChevronRight
          className={cn("h-3 w-3 transition-transform", open && "rotate-90")}
        />
        thinking
      </span>
      {open && (
        <p className="mt-1 border-l border-neutral-200 pl-3 text-[13px] italic leading-5 text-neutral-500 whitespace-pre-wrap">
          {text}
        </p>
      )}
    </button>
  );
}

function ToolBlock({ part }: { part: ToolPart }) {
  const [open, setOpen] = React.useState(false);
  return (
    <button onClick={() => setOpen(!open)} className="block w-full text-left my-1">
      <span className="inline-flex items-center gap-1.5 rounded-full border border-neutral-300 px-2.5 py-0.5 text-[11px] font-mono text-neutral-600">
        <Wrench className="h-3 w-3" />
        {part.name}
        {part.output === undefined && (
          <span className="animate-pulse text-neutral-400">…</span>
        )}
      </span>
      {open && (
        <div className="mt-1 border-l border-neutral-200 pl-3 font-mono text-[12px] leading-5 text-neutral-500">
          <p className="whitespace-pre-wrap break-all">
            → {JSON.stringify(part.input)}
          </p>
          {part.output !== undefined && (
            <p className="mt-1 whitespace-pre-wrap">{part.output}</p>
          )}
        </div>
      )}
    </button>
  );
}

function Bubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === "user";
  if (isUser) {
    return (
      <div className="flex flex-col items-end">
        <div className="max-w-[75%] rounded-3xl rounded-br-md bg-black px-4 py-2 text-[15px] leading-5 text-white whitespace-pre-wrap">
          {textOf(msg)}
        </div>
        <span className="mt-1 pr-1 text-[10px] text-neutral-400">{msg.time}</span>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-start">
      <div className="max-w-[85%] w-fit">
        {msg.parts.map((p, i) =>
          p.kind === "thinking" ? (
            <ThinkingBlock key={i} text={p.text} />
          ) : p.kind === "tool" ? (
            <ToolBlock key={i} part={p} />
          ) : p.text ? (
            <div
              key={i}
              className="my-1 rounded-3xl rounded-bl-md border border-neutral-200 bg-white px-4 py-2 text-[15px] leading-5 text-black whitespace-pre-wrap"
            >
              {p.text}
            </div>
          ) : null
        )}
      </div>
      <span className="mt-0.5 pl-1 text-[10px] text-neutral-400">{msg.time}</span>
    </div>
  );
}

/* ---------------------------------------------------------------- chat */

export function Chat() {
  const [messages, setMessages] = React.useState<Msg[]>([]);
  const [input, setInput] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const endRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const appendToAssistant = (fn: (parts: Part[]) => Part[]) =>
    setMessages((ms) => {
      const copy = [...ms];
      const last = copy[copy.length - 1];
      if (last?.role === "assistant") {
        copy[copy.length - 1] = { ...last, parts: fn(last.parts) };
      }
      return copy;
    });

  const mergeDelta = (kind: "text" | "thinking", text: string) =>
    appendToAssistant((parts) => {
      const last = parts[parts.length - 1];
      if (last && last.kind === kind) {
        return [...parts.slice(0, -1), { kind, text: last.text + text }];
      }
      return [...parts, { kind, text }];
    });

  async function send() {
    const content = input.trim();
    if (!content || busy) return;
    setInput("");
    setBusy(true);

    const history = [
      ...messages
        .filter((m) => textOf(m).length > 0)
        .map((m) => ({ role: m.role, content: textOf(m) })),
      { role: "user" as const, content },
    ];

    setMessages((ms) => [
      ...ms,
      { role: "user", parts: [{ kind: "text", text: content }], time: now() },
      { role: "assistant", parts: [], time: now() },
    ]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });
      if (!res.ok || !res.body) throw new Error(`backend ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";
        for (const chunk of chunks) {
          const line = chunk.trim();
          if (!line.startsWith("data: ")) continue;
          const evt: SseEvent = JSON.parse(line.slice(6));
          if (evt.type === "text_delta") mergeDelta("text", evt.text);
          else if (evt.type === "thinking_delta") mergeDelta("thinking", evt.text);
          else if (evt.type === "tool_call")
            appendToAssistant((parts) => [
              ...parts,
              { kind: "tool", id: evt.id, name: evt.name, input: evt.input },
            ]);
          else if (evt.type === "tool_result")
            appendToAssistant((parts) =>
              parts.map((p) =>
                p.kind === "tool" && p.id === evt.id ? { ...p, output: evt.output } : p
              )
            );
          else if (evt.type === "error")
            appendToAssistant((parts) => [
              ...parts,
              { kind: "text", text: `⚠ ${evt.message}` },
            ]);
        }
      }
    } catch (err) {
      appendToAssistant((parts) => [
        ...parts,
        { kind: "text", text: `⚠ ${err instanceof Error ? err.message : err}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex h-dvh max-w-2xl flex-col">
      <header className="border-b border-neutral-200 px-6 py-3 text-center">
        <h1 className="text-sm font-semibold tracking-tight">gmail-mcp</h1>
        <p className="text-[11px] text-neutral-400">inbox cleanup, chat only</p>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-6">
        {messages.length === 0 && (
          <p className="pt-24 text-center text-[13px] text-neutral-400">
            Try: &ldquo;find promotional emails older than 6 months and help me
            unsubscribe&rdquo;
          </p>
        )}
        {messages.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}
        {busy && (
          <p className="pl-1 text-[11px] text-neutral-400 animate-pulse">…</p>
        )}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
        className="flex items-end gap-2 border-t border-neutral-200 px-4 py-3"
      >
        <Textarea
          rows={1}
          value={input}
          placeholder="Message"
          disabled={busy}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
        />
        <Button type="submit" disabled={busy || !input.trim()} aria-label="Send">
          <ArrowUp className="h-4 w-4" />
        </Button>
      </form>
    </main>
  );
}
