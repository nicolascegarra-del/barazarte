"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { API_URL, ApiError, parseResponse } from "./api";

export interface Me { id: number; email: string; display_name: string }
interface TokenResponse { access_token: string; artist: Me }
type Init = Omit<RequestInit, "body"> & { json?: unknown; body?: BodyInit };

interface SessionValue {
  artist: Me | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  authFetch: <T>(path: string, init?: Init) => Promise<T>;
}
const Ctx = createContext<SessionValue | null>(null);

/**
 * Sesión del artista. El access token vive solo en memoria (nunca en localStorage);
 * el refresh token es una cookie HttpOnly que el navegador envía a /auth/refresh.
 */
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const token = useRef<string | null>(null);
  const [artist, setArtist] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  const apply = (t: TokenResponse | null) => {
    token.current = t?.access_token ?? null;
    setArtist(t?.artist ?? null);
  };

  const refresh = useCallback(async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_URL}/auth/refresh`, { method: "POST", credentials: "include" });
      if (!res.ok) return false;
      apply((await res.json()) as TokenResponse);
      return true;
    } catch {
      return false;
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    apply(await parseResponse<TokenResponse>(res));
  }, []);

  const logout = useCallback(async () => {
    await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" }).catch(() => undefined);
    apply(null);
  }, []);

  const authFetch = useCallback(
    async <T,>(path: string, init: Init = {}): Promise<T> => {
      const run = () => {
        const headers = new Headers(init.headers);
        if (token.current) headers.set("Authorization", `Bearer ${token.current}`);
        if (init.json !== undefined) headers.set("Content-Type", "application/json");
        return fetch(`${API_URL}${path}`, {
          ...init,
          headers,
          credentials: "include",
          body: init.json !== undefined ? JSON.stringify(init.json) : init.body,
        });
      };
      let res = await run();
      if (res.status === 401 && (await refresh())) res = await run(); // token caducado: renovar y reintentar una vez
      if (res.status === 401) apply(null);
      return parseResponse<T>(res);
    },
    [refresh],
  );

  const value = useMemo(() => ({ artist, loading, login, logout, authFetch }), [artist, loading, login, logout, authFetch]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useSession debe usarse dentro de SessionProvider");
  return v;
}

export { ApiError };
