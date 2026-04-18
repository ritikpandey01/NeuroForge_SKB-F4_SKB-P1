import { ReactNode } from "react";

import { PeriodProvider } from "@/contexts/PeriodContext";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <PeriodProvider>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-6 py-6">{children}</main>
        </div>
      </div>
    </PeriodProvider>
  );
}
