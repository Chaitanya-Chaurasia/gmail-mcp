"use client";

import * as React from "react";
import { GripVertical, Play, X } from "lucide-react";
import { cn } from "@/lib/utils";

/* ---------------------------------------------------------------- types */

type Schema = {
  type: string;
  properties?: Record<string, { type?: string; description?: string; default?: unknown }>;
  required?: string[];
};

type ToolDef = { name: string; description: string; input_schema: Schema };

type CardState = {
  uid: number;
  tool: ToolDef;
  values: Record<string, string>;
  output?: string;
  running: boolean;
  confirming: boolean;
};

const DESTRUCTIVE = new Set([
  "trash_email",
  "trash_many",
  "report_spam",
  "send_unsubscribe",
  "block_sender",
]);

/* --------------------------------------------------------- form helpers */

function coerce(schema: Schema, values: Record<string, string>) {
  const args: Record<string, unknown> = {};
  for (const [key, prop] of Object.entries(schema.properties ?? {})) {
    const raw = values[key];
    if (raw === undefined || raw === "") continue;
    if (prop.type === "integer" || prop.type === "number") args[key] = Number(raw);
    else if (prop.type === "array")
      args[key] = raw
        .split(/[\n,]/)
        .map((s) => s.trim())
        .filter(Boolean);
    else args[key] = raw;
  }
  return args;
}

/* ---------------------------------------------------------------- card */

function ToolCard({
  card,
  onChange,
  onRemove,
  onRun,
}: {
  card: CardState;
  onChange: (uid: number, patch: Partial<CardState>) => void;
  onRemove: (uid: number) => void;
  onRun: (uid: number) => void;
}) {
  const { tool, values, output, running, confirming } = card;
  const destructive = DESTRUCTIVE.has(tool.name);
  const props = Object.entries(tool.input_schema.properties ?? {});
  const required = new Set(tool.input_schema.required ?? []);

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-mono text-[13px] font-semibold">
            {tool.name}
            {destructive && (
              <span className="ml-2 rounded-full border border-black px-1.5 py-px text-[9px] font-sans uppercase tracking-wider">
                destructive
              </span>
            )}
          </p>
          <p className="mt-0.5 text-[11px] leading-4 text-neutral-500">
            {tool.description.split("\n")[0]}
          </p>
        </div>
        <button
          onClick={() => onRemove(card.uid)}
          aria-label="Remove"
          className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-black"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {props.length > 0 && (
        <div className="mt-3 space-y-2">
          {props.map(([key, prop]) => (
            <label key={key} className="block">
              <span className="mb-0.5 block font-mono text-[10px] text-neutral-500">
                {key}
                {required.has(key) && " *"}
                {prop.type === "array" && "  (one per line)"}
              </span>
              {prop.type === "array" ? (
                <textarea
                  rows={3}
                  value={values[key] ?? ""}
                  onChange={(e) =>
                    onChange(card.uid, { values: { ...values, [key]: e.target.value } })
                  }
                  className="w-full rounded-lg border border-neutral-300 px-2 py-1.5 font-mono text-[12px] focus:border-black focus:outline-none"
                />
              ) : (
                <input
                  type={prop.type === "integer" || prop.type === "number" ? "number" : "text"}
                  value={values[key] ?? ""}
                  placeholder={prop.default !== undefined ? String(prop.default) : ""}
                  onChange={(e) =>
                    onChange(card.uid, { values: { ...values, [key]: e.target.value } })
                  }
                  className="w-full rounded-lg border border-neutral-300 px-2 py-1.5 font-mono text-[12px] focus:border-black focus:outline-none"
                />
              )}
            </label>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => {
            if (destructive && !confirming) onChange(card.uid, { confirming: true });
            else onRun(card.uid);
          }}
          disabled={running}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12px] transition-colors",
            confirming
              ? "bg-black text-white"
              : "border border-black text-black hover:bg-black hover:text-white",
            running && "pointer-events-none opacity-40"
          )}
        >
          <Play className="h-3 w-3" />
          {running ? "running…" : confirming ? "click again to confirm" : "run"}
        </button>
        {confirming && !running && (
          <button
            onClick={() => onChange(card.uid, { confirming: false })}
            className="text-[12px] text-neutral-400 hover:text-black"
          >
            cancel
          </button>
        )}
      </div>

      {output !== undefined && (
        <pre className="mt-3 max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg border border-neutral-200 bg-neutral-50 p-3 font-mono text-[11px] leading-4 text-neutral-800">
          {output}
        </pre>
      )}
    </div>
  );
}

/* ------------------------------------------------------------ workbench */

export function Workbench() {
  const [tools, setTools] = React.useState<ToolDef[]>([]);
  const [cards, setCards] = React.useState<CardState[]>([]);
  const [error, setError] = React.useState<string>();
  const [dragOver, setDragOver] = React.useState(false);
  const uidRef = React.useRef(1);

  React.useEffect(() => {
    fetch("/api/tools")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`backend ${r.status}`))))
      .then(setTools)
      .catch((e) => setError(String(e)));
  }, []);

  const addCard = (name: string) => {
    const tool = tools.find((t) => t.name === name);
    if (!tool) return;
    setCards((cs) => [
      ...cs,
      { uid: uidRef.current++, tool, values: {}, running: false, confirming: false },
    ]);
  };

  const patchCard = (uid: number, patch: Partial<CardState>) =>
    setCards((cs) => cs.map((c) => (c.uid === uid ? { ...c, ...patch } : c)));

  const runCard = async (uid: number) => {
    const card = cards.find((c) => c.uid === uid);
    if (!card) return;
    patchCard(uid, { running: true, confirming: false, output: undefined });
    try {
      const res = await fetch(`/api/tools/${card.tool.name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(coerce(card.tool.input_schema, card.values)),
      });
      const data = await res.json();
      patchCard(uid, {
        running: false,
        output: res.ok ? data.output : `error: ${JSON.stringify(data)}`,
      });
    } catch (e) {
      patchCard(uid, { running: false, output: `error: ${e}` });
    }
  };

  return (
    <div className="flex h-dvh">
      {/* palette */}
      <div className="w-56 shrink-0 overflow-y-auto border-r border-neutral-200 px-3 py-4">
        <p className="mb-2 px-1 text-[10px] uppercase tracking-wider text-neutral-400">
          tools - drag onto canvas
        </p>
        {error && <p className="px-1 text-[11px] text-neutral-500">⚠ {error}</p>}
        <div className="space-y-1">
          {tools.map((t) => (
            <div
              key={t.name}
              draggable
              onDragStart={(e) => e.dataTransfer.setData("text/tool", t.name)}
              onDoubleClick={() => addCard(t.name)}
              title={t.description.split("\n")[0]}
              className={cn(
                "flex cursor-grab items-center gap-1.5 rounded-lg border border-neutral-200",
                "px-2 py-1.5 font-mono text-[12px] text-neutral-700 active:cursor-grabbing",
                "hover:border-black hover:text-black",
                DESTRUCTIVE.has(t.name) && "border-dashed"
              )}
            >
              <GripVertical className="h-3 w-3 shrink-0 text-neutral-300" />
              {t.name}
            </div>
          ))}
        </div>
      </div>

      {/* canvas */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const name = e.dataTransfer.getData("text/tool");
          if (name) addCard(name);
        }}
        className={cn(
          "flex-1 overflow-y-auto p-6 transition-colors",
          dragOver && "bg-neutral-50"
        )}
      >
        {cards.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="rounded-2xl border border-dashed border-neutral-300 px-10 py-16 text-center text-[13px] text-neutral-400">
              drop a tool here
              <br />
              <span className="text-[11px]">(or double-click one in the palette)</span>
            </p>
          </div>
        ) : (
          <div className="mx-auto max-w-xl space-y-4">
            {cards.map((c) => (
              <ToolCard
                key={c.uid}
                card={c}
                onChange={patchCard}
                onRemove={(uid) => setCards((cs) => cs.filter((x) => x.uid !== uid))}
                onRun={runCard}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
