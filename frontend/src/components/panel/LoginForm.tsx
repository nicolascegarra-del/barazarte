"use client";

import Link from "next/link";
import { useState } from "react";
import { useSession } from "@/lib/session";

const field = "w-full min-h-12 rounded-md border border-line bg-white px-3 text-base outline-none focus:border-gold";

export function LoginForm() {
  const { login } = useSession();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await login(String(f.get("email")), String(f.get("password")));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-sm space-y-4 py-8">
      <h1 className="font-serif text-3xl">Acceso para artistas</h1>
      <p className="text-sm text-muted">Entra para subir y gestionar tus obras.</p>
      <div>
        <label htmlFor="email" className="mb-1 block text-xs">Email</label>
        <input id="email" name="email" type="email" required autoComplete="username" className={field} />
      </div>
      <div>
        <label htmlFor="password" className="mb-1 block text-xs">Contraseña</label>
        <input id="password" name="password" type="password" required autoComplete="current-password" className={field} />
      </div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button disabled={busy} className="min-h-12 w-full bg-foreground text-xs uppercase tracking-[0.18em] text-background disabled:opacity-60">
        {busy ? "Entrando…" : "Entrar"}
      </button>
      <div className="flex flex-col gap-1 text-center text-sm text-muted">
        <Link href="/recuperar" className="min-h-11 content-center underline">¿Olvidaste la contraseña?</Link>
        <span>¿Aún no tienes cuenta? <Link href="/registro" className="underline">Regístrate como artista</Link></span>
      </div>
    </form>
  );
}
