"use client";

import { useEffect, useState } from "react";
import { type EmailSettings } from "@/lib/api";
import { useSession } from "@/lib/session";

const field = "min-h-12 w-full rounded-md border border-line bg-white px-3 text-base outline-none focus:border-gold md:text-sm";

const PRESETS: Record<string, { port: number; security: EmailSettings["security"] }> = {
  "587": { port: 587, security: "starttls" },
  "465": { port: 465, security: "ssl" },
  "25": { port: 25, security: "none" },
};

/** Cuenta de correo única de la plataforma: con ella se envían todos los emails a artistas y compradores. */
export default function AdminCorreo() {
  const { authFetch, artist } = useSession();
  const [s, setS] = useState<EmailSettings | null>(null);
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    authFetch<EmailSettings>("/admin/email-settings").then(setS).catch(() => setMsg({ ok: false, text: "No se pudo cargar la configuración." }));
  }, [authFetch]);

  if (!s) return <p className="text-sm text-muted">{msg ? msg.text : "Cargando…"}</p>;
  const set = <K extends keyof EmailSettings>(k: K, v: EmailSettings[K]) => setS({ ...s, [k]: v });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!s) return;
    setBusy(true);
    setMsg(null);
    try {
      const body = {
        host: s.host.trim(), port: Number(s.port), username: s.username?.trim() || null,
        security: s.security, from_name: s.from_name.trim(), from_email: s.from_email.trim(),
        ...(password ? { password } : {}), // sin contraseña nueva se conserva la actual
      };
      setS(await authFetch<EmailSettings>("/admin/email-settings", { method: "PUT", json: body }));
      setPassword("");
      setMsg({ ok: true, text: "Configuración guardada." });
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : "No se pudo guardar." });
    } finally {
      setBusy(false);
    }
  }

  async function sendTest() {
    setBusy(true);
    setMsg(null);
    try {
      await authFetch("/admin/email-settings/test", { method: "POST", json: {} });
      setMsg({ ok: true, text: `Email de prueba enviado a ${artist?.email}. Revisa tu bandeja.` });
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : "No se pudo enviar el email de prueba." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1 className="font-serif text-3xl md:text-4xl">Correo de la plataforma</h1>
      <p className="mt-1 max-w-xl text-sm text-muted">
        Una única cuenta envía todos los emails: verificación de cuentas, recuperación de contraseña y avisos a los artistas
        cuando alguien les escribe. Cuando un artista responde, lo hace directamente al comprador.
      </p>
      {s.source === "environment" && (
        <p className="mt-4 max-w-xl border border-line bg-white p-3 text-sm">
          Ahora mismo se usa la configuración por defecto del servidor. Guarda este formulario para usar tu propia cuenta.
        </p>
      )}

      <form onSubmit={save} className="mt-6 max-w-xl space-y-4">
        <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_120px]">
          <div>
            <label htmlFor="host" className="mb-1 block text-xs">Servidor SMTP</label>
            <input id="host" required value={s.host} onChange={(e) => set("host", e.target.value)} placeholder="smtp.tuproveedor.com" className={field} />
          </div>
          <div>
            <label htmlFor="port" className="mb-1 block text-xs">Puerto</label>
            <input id="port" required inputMode="numeric" value={s.port} onChange={(e) => set("port", Number(e.target.value.replace(/\D/g, "")))} className={field} />
          </div>
        </div>

        <fieldset>
          <legend className="mb-1 text-xs">Seguridad</legend>
          <div className="flex flex-wrap gap-2">
            {([["starttls", "STARTTLS (587)"], ["ssl", "SSL/TLS (465)"], ["none", "Ninguna"]] as const).map(([v, label]) => (
              <button
                key={v} type="button" aria-pressed={s.security === v}
                onClick={() => setS({ ...s, security: v, port: v === "starttls" ? PRESETS["587"].port : v === "ssl" ? PRESETS["465"].port : PRESETS["25"].port })}
                className={`min-h-11 border px-3 text-sm ${s.security === v ? "border-gold text-gold" : "border-line"}`}
              >
                {label}
              </button>
            ))}
          </div>
        </fieldset>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="user" className="mb-1 block text-xs">Usuario</label>
            <input id="user" autoComplete="off" value={s.username ?? ""} onChange={(e) => set("username", e.target.value)} className={field} />
          </div>
          <div>
            <label htmlFor="pw" className="mb-1 block text-xs">Contraseña</label>
            <input
              id="pw" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder={s.has_password ? "•••••••• (guardada)" : ""} className={field}
            />
            <p className="mt-1 text-[11px] text-muted">Déjala vacía para conservar la actual. Nunca se muestra de nuevo.</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="fname" className="mb-1 block text-xs">Nombre del remitente</label>
            <input id="fname" required value={s.from_name} onChange={(e) => set("from_name", e.target.value)} className={field} />
          </div>
          <div>
            <label htmlFor="femail" className="mb-1 block text-xs">Email del remitente</label>
            <input id="femail" type="email" required value={s.from_email} onChange={(e) => set("from_email", e.target.value)} className={field} />
          </div>
        </div>

        {msg && <p role={msg.ok ? "status" : "alert"} className={`text-sm ${msg.ok ? "text-gold" : "text-red-700"}`}>{msg.text}</p>}

        <div className="flex flex-wrap gap-3">
          <button disabled={busy} className="min-h-12 bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background disabled:opacity-60">Guardar</button>
          <button type="button" disabled={busy} onClick={sendTest} className="min-h-12 border border-line px-6 text-sm disabled:opacity-60">Enviarme un email de prueba</button>
        </div>
        <p className="text-[11px] text-muted">Guarda antes de enviar la prueba: se usa la configuración guardada.</p>
      </form>
    </>
  );
}
