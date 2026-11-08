"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { publicPost } from "@/lib/api";

/** Confirma el email con el token del enlace. El useRef evita doble llamada en modo desarrollo (token de un solo uso). */
export function VerifyEmail() {
  const token = useSearchParams().get("token");
  const done = useRef(false);
  const [state, setState] = useState<"loading" | "ok" | "error">(token ? "loading" : "error");
  const [msg, setMsg] = useState("El enlace no es válido.");

  useEffect(() => {
    if (!token || done.current) return;
    done.current = true;
    publicPost("/auth/verify-email", { token })
      .then(() => setState("ok"))
      .catch((e) => { setMsg(e instanceof Error ? e.message : msg); setState("error"); });
  }, [token, msg]);

  if (state === "loading") return <p className="text-sm text-muted">Verificando tu email…</p>;
  if (state === "ok")
    return (
      <div role="status" className="space-y-4 text-sm">
        <p>Tu cuenta está activada. Ya puedes subir tus obras.</p>
        <Link href="/panel" className="inline-flex min-h-12 items-center bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background">Entrar al panel</Link>
      </div>
    );
  return (
    <div role="alert" className="space-y-3 text-sm">
      <p className="text-red-700">{msg}</p>
      <p className="text-muted">El enlace puede haber caducado. Vuelve a registrarte para recibir uno nuevo.</p>
      <Link href="/registro" className="underline">Ir al registro</Link>
    </div>
  );
}
