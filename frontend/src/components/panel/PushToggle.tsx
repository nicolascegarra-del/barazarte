"use client";

import { useCallback, useEffect, useState } from "react";
import { BellOff, BellRing, Share } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useSession } from "@/lib/session";

type State = "loading" | "unsupported" | "ios-install" | "denied" | "off" | "on" | "server-off";

/** Clave VAPID en base64url → bytes, como la pide `pushManager.subscribe`. */
function keyToBytes(base64url: string): Uint8Array<ArrayBuffer> {
  const pad = "=".repeat((4 - (base64url.length % 4)) % 4);
  const raw = atob((base64url + pad).replace(/-/g, "+").replace(/_/g, "/"));
  const out = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

const isIOS = () => /iPad|iPhone|iPod/.test(navigator.userAgent);
const isStandalone = () =>
  window.matchMedia("(display-mode: standalone)").matches || (navigator as Navigator & { standalone?: boolean }).standalone === true;

/**
 * Activa o desactiva las notificaciones en este dispositivo.
 * En iPhone, Apple solo las permite si la web está añadida a la pantalla de inicio.
 */
export function PushToggle() {
  const { authFetch } = useSession();
  const [state, setState] = useState<State>("loading");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const supported = () => typeof window !== "undefined" && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;

  const check = useCallback(async () => {
    if (!supported()) return setState(isIOS() && !isStandalone() ? "ios-install" : "unsupported");
    if (Notification.permission === "denied") return setState("denied");
    const reg = await navigator.serviceWorker.getRegistration("/");
    const sub = await reg?.pushManager.getSubscription();
    if (sub) {
      // Asegura que el servidor tiene esta suscripción asociada al artista que ha iniciado sesión.
      await authFetch("/panel/push/subscribe", { method: "POST", json: sub.toJSON() }).catch(() => undefined);
      return setState("on");
    }
    setState("off");
  }, [authFetch]);

  useEffect(() => {
    void check();
  }, [check]);

  async function enable() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/push/public-key`);
      const { public_key } = (await res.json()) as { public_key: string | null };
      if (!public_key) return setState("server-off");
      const permission = await Notification.requestPermission();
      if (permission !== "granted") return setState(permission === "denied" ? "denied" : "off");
      const reg = await navigator.serviceWorker.register("/sw.js", { scope: "/" });
      await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyToBytes(public_key) });
      await authFetch("/panel/push/subscribe", { method: "POST", json: sub.toJSON() });
      setState("on");
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron activar los avisos.");
    } finally {
      setBusy(false);
    }
  }

  async function disable() {
    setBusy(true);
    try {
      const reg = await navigator.serviceWorker.getRegistration("/");
      const sub = await reg?.pushManager.getSubscription();
      if (sub) {
        await authFetch("/panel/push/unsubscribe", { method: "POST", json: { endpoint: sub.endpoint } }).catch(() => undefined);
        await sub.unsubscribe();
      }
      setState("off");
    } finally {
      setBusy(false);
    }
  }

  if (state === "loading") return null;

  const box = "border border-line bg-white p-4 text-sm";
  if (state === "on")
    return (
      <div className={`${box} flex flex-wrap items-center justify-between gap-3`}>
        <p className="flex items-center gap-2"><BellRing size={18} className="text-gold" aria-hidden /> Avisos activados en este dispositivo.</p>
        <button type="button" disabled={busy} onClick={disable} className="min-h-11 px-2 text-xs text-muted underline">Desactivar</button>
      </div>
    );
  if (state === "off")
    return (
      <div className={box}>
        <p>Recibe un aviso en el móvil cada vez que alguien te escriba por una obra.</p>
        {error && <p role="alert" className="mt-2 text-xs text-red-700">{error}</p>}
        <button type="button" disabled={busy} onClick={enable} className="mt-3 inline-flex min-h-11 items-center gap-2 bg-foreground px-4 text-xs uppercase tracking-[0.15em] text-background disabled:opacity-60">
          <BellRing size={16} aria-hidden /> {busy ? "Activando…" : "Activar avisos"}
        </button>
      </div>
    );
  if (state === "ios-install")
    return (
      <div className={box}>
        <p className="font-medium">Para recibir avisos en tu iPhone</p>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-muted">
          <li>Pulsa <Share size={14} className="inline align-[-2px]" aria-label="Compartir" /> en Safari.</li>
          <li>Elige «Añadir a pantalla de inicio».</li>
          <li>Abre BarazArte desde ese icono y vuelve aquí para activar los avisos.</li>
        </ol>
      </div>
    );
  return (
    <div className={`${box} flex items-start gap-2 text-muted`}>
      <BellOff size={18} className="mt-0.5 shrink-0" aria-hidden />
      <p>
        {state === "denied" && "Has bloqueado las notificaciones para esta web. Actívalas en los ajustes del navegador para recibir avisos."}
        {state === "unsupported" && "Este navegador no admite avisos. Prueba con Chrome en Android o con la app añadida a la pantalla de inicio en iPhone."}
        {state === "server-off" && "Los avisos aún no están configurados en el servidor."}
      </p>
    </div>
  );
}
