import {
  AlertTriangle,
  BarChart3,
  Database,
  FileText,
  Gauge,
  History,
  Leaf,
  Settings,
  Sprout,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAnomalySummary } from "@/features/anomalies/api";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/data", label: "Data Management", icon: Database },
  { to: "/emissions", label: "Emissions", icon: BarChart3 },
  { to: "/suppliers", label: "Suppliers", icon: Users },
  { to: "/anomalies", label: "Anomalies", icon: AlertTriangle },
  { to: "/scenarios", label: "Scenarios", icon: Sprout },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/audit", label: "Audit Log", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const anomalySummary = useAnomalySummary();
  const openAnomalies = anomalySummary.data?.open_count ?? 0;

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-brand text-white">
          <Leaf size={18} />
        </div>
        <div>
          <div className="text-sm font-semibold tracking-tight text-slate-900">CarbonLens</div>
          <div className="text-[10px] uppercase tracking-widest text-slate-400">ESG & GHG</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center justify-between gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 text-brand-800"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
              )
            }
          >
            <span className="flex items-center gap-3">
              <Icon size={16} />
              {label}
            </span>
            {to === "/anomalies" && openAnomalies > 0 && (
              <span className="inline-flex min-w-[18px] items-center justify-center rounded-full bg-red-600 px-1.5 text-[10px] font-semibold text-white">
                {openAnomalies}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-200 px-5 py-3 text-[11px] text-slate-400">
        v0.1.0 · Demo build
      </div>
    </aside>
  );
}
