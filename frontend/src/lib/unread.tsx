"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useSession } from "./session";

interface UnreadValue {
  count: number;
  refresh: () => Promise<void>;
  markAllRead: () => Promise<void>;
}
const Ctx = createContext<UnreadValue>({ count: 0, refresh: async () => {}, markAllRead: async () => {} });

const POLL_MS = 60_000;

/** Número en el icono de la app instalada (Android/iOS con la web en pantalla de inicio), si el navegador lo admite. */
function setAppBadge(count: number) {
  const nav = navigator as Navigator & { setAppBadge?: (n: number) => Promise<void>; clearAppBadge?: () => Promise<void> };
  if (count > 0) nav.setAppBadge?.(count).catch(() => undefined);
  else nav.clearAppBadge?.().catch(() => undefined);
}

/**
 * Consultas sin leer del artista: se actualiza cada minuto, al volver a la pestaña
 * y cuando el service worker avisa de una notificación push recibida.
 */
export function UnreadProvider({ children }: { children: React.ReactNode }) {
  const { artist, authFetch } = useSession();
  const [count, setCount] = useState(0);

  const apply = useCallback((n: number) => {
    setCount(n);
    setAppBadge(n);
  }, []);

  const refresh = useCallback(async () => {
    if (!artist) return;
    try {
      apply((await authFetch<{ count: number }>("/panel/inquiries/unread-count")).count);
    } catch {
      /* sin conexión: se mantiene el último valor */
    }
  }, [artist, authFetch, apply]);

  const markAllRead = useCallback(async () => {
    if (!artist) return;
    try {
      await authFetch("/panel/inquiries/read-all", { method: "POST" });
      apply(0);
    } catch {
      /* se reintentará en la próxima visita */
    }
  }, [artist, authFetch, apply]);

  useEffect(() => {
    if (!artist) return;
    void refresh();
    const timer = setInterval(refresh, POLL_MS);
    const onVisible = () => document.visibilityState === "visible" && void refresh();
    const onMessage = (e: MessageEvent) => e.data?.type === "push" && void refresh();
    document.addEventListener("visibilitychange", onVisible);
    navigator.serviceWorker?.addEventListener("message", onMessage);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      navigator.serviceWorker?.removeEventListener("message", onMessage);
    };
  }, [artist, refresh]);

  const value = useMemo(() => ({ count, refresh, markAllRead }), [count, refresh, markAllRead]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useUnread = () => useContext(Ctx);
