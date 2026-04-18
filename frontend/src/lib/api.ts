const API_BASE = "/api/v1";

const ACCESS_KEY = "carbonlens.access";
const REFRESH_KEY = "carbonlens.refresh";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export const tokenStore = {
  getAccess: (): string | null => localStorage.getItem(ACCESS_KEY),
  getRefresh: (): string | null => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

// Invoked on 401-after-refresh-failure so the UI can redirect to /login.
let onAuthExpired: (() => void) | null = null;
export function setAuthExpiredHandler(fn: () => void) {
  onAuthExpired = fn;
}

async function rawFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const access = tokenStore.getAccess();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (access) headers["Authorization"] = `Bearer ${access}`;
  return fetch(url, { ...init, headers });
}

let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return false;
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = (await res.json()) as { access_token: string; refresh_token: string };
      tokenStore.set(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res = await rawFetch(path, init);
  if (res.status === 401 && !path.startsWith("/auth/")) {
    const ok = await tryRefresh();
    if (ok) {
      res = await rawFetch(path, init);
    } else {
      tokenStore.clear();
      onAuthExpired?.();
    }
  }
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
