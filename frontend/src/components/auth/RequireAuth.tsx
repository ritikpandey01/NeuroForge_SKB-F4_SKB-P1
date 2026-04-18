import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { Role, useAuth } from "@/contexts/AuthContext";

interface Props {
  children: ReactNode;
  roles?: Role[];
}

export function RequireAuth({ children, roles }: Props) {
  const { user, status, hasRole } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <div className="flex h-screen w-screen items-center justify-center text-sm text-slate-500">
        Loading...
      </div>
    );
  }

  if (status === "anonymous" || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (roles && !hasRole(...roles)) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 py-20 text-center">
        <div className="text-base font-semibold text-slate-900">Access denied</div>
        <div className="max-w-sm text-sm text-slate-500">
          This page is restricted to: {roles.join(", ")}. You are signed in as{" "}
          <span className="font-medium">{user.role}</span>.
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
