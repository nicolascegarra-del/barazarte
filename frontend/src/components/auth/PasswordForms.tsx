"use client";

import Link from "next/link";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { publicPost } from "@/lib/api";
import { authButton, authField } from "./AuthCard";

/** Paso 1: pedir el enlace. La respuesta es siempre la misma para no revelar qué emails existen. */
export function RequestReset() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const email = String(new FormData(e.currentTarget).get("email"));
    setBusy(true);
    setError(null);
    try {
      await publicPost("/auth/password-reset/request", { email });
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo enviar el email.");
    } finally {
      setBusy(false);
    }
  }

  if (sent)
    return <p role="status" className="text-sm">Si existe una cuenta con ese email, te hemos enviado un enlace para elegir una contraseña nueva. Caduca en 1 hora.</p>;
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="mb-1 block text-xs">Email</label>
        <input id="email" name="email" type="email" required autoComplete="email" className={authField} />
      </div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button disabled={busy} className={authButton}>{busy ? "Enviando…" : "Enviar enlace"}</button>
    </form>
  );
}

/** Paso 2: elegir la contraseña nueva con el token del enlace. */
export function ConfirmReset() {
  const token = useSearchParams().get("token");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!token) return <p role="alert" className="text-sm text-red-700">El enlace no es válido. <Link href="/recuperar" className="underline">Pide uno nuevo</Link>.</p>;
  if (done)
    return (
      <div role="status" className="space-y-4 text-sm">
        <p>Contraseña actualizada.</p>
        <Link href="/panel" className="inline-flex min-h-12 items-center bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background">Entrar</Link>
      </div>
    );

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const pw = String(f.get("password"));
    if (pw.length < 10) return setError("Mínimo 10 caracteres.");
    if (pw !== String(f.get("confirm"))) return setError("Las contraseñas no coinciden.");
    setBusy(true);
    setError(null);
    try {
      await publicPost("/auth/password-reset/confirm", { token, new_password: pw });
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar la contraseña.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="password" className="mb-1 block text-xs">Contraseña nueva</label>
        <input id="password" name="password" type="password" required autoComplete="new-password" className={authField} />
      </div>
      <div>
        <label htmlFor="confirm" className="mb-1 block text-xs">Repítela</label>
        <input id="confirm" name="confirm" type="password" required autoComplete="new-password" className={authField} />
      </div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button disabled={busy} className={authButton}>{busy ? "Guardando…" : "Guardar contraseña"}</button>
    </form>
  );
}
