import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { api, setAuthExpiredHandler, tokenStore } from "@/lib/api";

export type Role = "admin" | "analyst" | "viewer";

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  org_id: number;
  is_active: boolean;
  created_at: string;
}

interface MeResponse {
  user: AuthUser;
  organization_name: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  orgName: string;
  status: "loading" | "authenticated" | "anonymous";
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [orgName, setOrgName] = useState("");
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");

  const loadMe = useCallback(async () => {
    try {
      const me = await api.get<MeResponse>("/auth/me");
      setUser(me.user);
      setOrgName(me.organization_name);
      setStatus("authenticated");
    } catch {
      setUser(null);
      setOrgName("");
      setStatus("anonymous");
    }
  }, []);

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setOrgName("");
    setStatus("anonymous");
  }, []);

  useEffect(() => {
    setAuthExpiredHandler(() => {
      setUser(null);
      setOrgName("");
      setStatus("anonymous");
    });
    if (tokenStore.getAccess()) {
      void loadMe();
    } else {
      setStatus("anonymous");
    }
  }, [loadMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await api.post<TokenResponse>("/auth/login", {
        email,
        password,
      });
      tokenStore.set(tokens.access_token, tokens.refresh_token);
      await loadMe();
    },
    [loadMe],
  );

  const hasRole = useCallback(
    (...roles: Role[]) => !!user && roles.includes(user.role),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({ user, orgName, status, login, logout, hasRole }),
    [user, orgName, status, login, logout, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
