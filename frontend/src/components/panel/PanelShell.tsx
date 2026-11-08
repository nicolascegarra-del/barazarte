"use client";

import { Logo } from "@/components/Logo";
import { SessionProvider, useSession } from "@/lib/session";
import { LoginForm } from "./LoginForm";
import { PanelNav } from "./PanelNav";

function Gate({ children, admin }: { children: React.ReactNode; admin: boolean }) {
  const { artist, loading, logout } = useSession();
  const denied = admin && artist && !artist.is_admin;

  return (
    <div className="min-h-screen pb-24 md:pb-0">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3 md:px-8">
          <Logo className="text-2xl" />
          {artist && (
            <div className="flex items-center gap-5">
              <PanelNav />
              <button onClick={logout} className="min-h-11 text-xs text-muted underline">Salir</button>
            </div>
          )}
        </div>
      </header>
      <div className="mx-auto max-w-5xl px-4 py-6 md:px-8 md:py-10">
        {loading ? (
          <p className="py-10 text-center text-sm text-muted">Cargando…</p>
        ) : !artist ? (
          <LoginForm />
        ) : denied ? (
          <p role="alert" className="py-10 text-center text-sm">No tienes acceso a esta zona.</p>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

/** Protege el panel (y la zona admin con `admin`): sin sesión solo se muestra el formulario de acceso. */
export function PanelShell({ children, admin = false }: { children: React.ReactNode; admin?: boolean }) {
  return (
    <SessionProvider>
      <Gate admin={admin}>{children}</Gate>
    </SessionProvider>
  );
}
