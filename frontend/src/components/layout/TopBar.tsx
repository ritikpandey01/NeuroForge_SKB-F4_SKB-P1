import { Building2, LogOut } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

import { PeriodSelector } from "./PeriodSelector";

const ROLE_STYLES: Record<string, string> = {
  admin: "bg-brand-100 text-brand-800",
  analyst: "bg-blue-100 text-blue-800",
  viewer: "bg-slate-100 text-slate-600",
};

export function TopBar() {
  const { user, orgName, logout } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const onLogout = () => {
    logout();
    qc.clear();
    navigate("/login", { replace: true });
  };

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((p) => p[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex items-center gap-3">
        <Building2 size={18} className="text-slate-400" />
        <div>
          <div className="text-sm font-semibold text-slate-900">
            {orgName || "CarbonLens"}
          </div>
          <div className="text-xs text-slate-500">
            {user ? user.email : "Not signed in"}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <PeriodSelector />
        {user && (
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2 py-1 pr-3 text-xs">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand text-[10px] font-semibold text-white">
              {initials}
            </div>
            <div className="flex flex-col leading-tight">
              <span className="font-medium text-slate-700">{user.full_name}</span>
              <span
                className={cn(
                  "w-fit rounded px-1.5 text-[10px] font-semibold uppercase tracking-wide",
                  ROLE_STYLES[user.role] ?? "bg-slate-100 text-slate-600",
                )}
              >
                {user.role}
              </span>
            </div>
            <button
              type="button"
              onClick={onLogout}
              title="Sign out"
              className="ml-1 rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            >
              <LogOut size={14} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
