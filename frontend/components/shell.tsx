"use client";

import * as React from "react";
import { Chat } from "@/components/chat";
import { Sidebar } from "@/components/sidebar";
import { Workbench } from "@/components/workbench";

export function Shell() {
  const [uiMode, setUiMode] = React.useState(false);

  return (
    <div className="flex h-dvh bg-white text-black">
      <Sidebar uiMode={uiMode} onToggleUiMode={setUiMode} />
      <div className="min-w-0 flex-1">{uiMode ? <Workbench /> : <Chat />}</div>
    </div>
  );
}
