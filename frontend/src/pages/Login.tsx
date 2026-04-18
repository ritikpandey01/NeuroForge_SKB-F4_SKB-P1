import { Leaf } from "lucide-react";
import { FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/lib/api";

interface LocationState {
  from?: { pathname: string };
}

const DEMO_LOGINS = [
  {
    org: "Greenfield Manufacturing",
    rows: [
      { role: "admin", email: "admin@greenfieldmfg.in" },
      { role: "analyst", email: "analyst@greenfieldmfg.in" },
      { role: "viewer", email: "viewer@greenfieldmfg.in" },
    ],
  },
  {
    org: "UltraTech Cement",
    rows: [
      { role: "admin", email: "admin@ultratechcement.com" },
      { role: "analyst", email: "analyst@ultratechcement.com" },
      { role: "viewer", email: "viewer@ultratechcement.com" },
    ],
  },
];

export default function Login() {
  const { login, status } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("carbonlens");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") {
    const from = (location.state as LocationState | null)?.from?.pathname ?? "/";
    return <Navigate to={from} replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim().toLowerCase(), password);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Invalid email or password.");
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen w-screen items-center justify-center bg-slate-50 px-4">
      <div className="grid w-full max-w-4xl gap-8 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="mb-6 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-brand text-white">
              <Leaf size={20} />
            </div>
            <div>
              <div className="text-base font-semibold tracking-tight text-slate-900">
                CarbonLens
              </div>
              <div className="text-[10px] uppercase tracking-widest text-slate-400">
                ESG &amp; GHG Monitoring
              </div>
            </div>
          </div>

          <h1 className="text-xl font-semibold text-slate-900">Sign in</h1>
          <p className="mt-1 text-sm text-slate-500">
            Use the demo credentials on the right — shared password{" "}
            <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-700">
              carbonlens
            </code>
            .
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-600">
                Email
              </span>
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
                placeholder="you@company.com"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-600">
                Password
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </label>
            {error && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-md bg-brand px-3 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {submitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Demo accounts</h2>
          <p className="mt-1 text-xs text-slate-500">
            Click any row to prefill the form.
          </p>
          <div className="mt-4 space-y-5">
            {DEMO_LOGINS.map((org) => (
              <div key={org.org}>
                <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  {org.org}
                </div>
                <div className="space-y-1">
                  {org.rows.map((row) => (
                    <button
                      key={row.email}
                      type="button"
                      onClick={() => setEmail(row.email)}
                      className="flex w-full items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-left text-xs hover:border-brand-500 hover:bg-brand-50"
                    >
                      <span className="font-medium capitalize text-slate-700">
                        {row.role}
                      </span>
                      <span className="font-mono text-slate-500">{row.email}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
