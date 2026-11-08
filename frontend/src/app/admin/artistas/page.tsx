"use client";

import { useCallback, useEffect, useState } from "react";
import { type AdminArtist, type Page } from "@/lib/api";
import { useSession } from "@/lib/session";

function ArtistRow({ a, onChange, onError }: { a: AdminArtist; onChange: () => void; onError: (m: string) => void }) {
  const { authFetch } = useSession();
  const [limit, setLimit] = useState(a.max_artworks === null ? "" : String(a.max_artworks));
  const [busy, setBusy] = useState(false);

  async function run(fn: () => Promise<unknown>, ok?: string) {
    setBusy(true);
    try {
      await fn();
      if (ok) window.alert(ok);
      onChange();
    } catch (e) {
      onError(e instanceof Error ? e.message : "No se pudo completar la acción.");
    } finally {
      setBusy(false);
    }
  }

  const patch = (json: object) => authFetch(`/admin/artists/${a.id}`, { method: "PATCH", json });
  const saveLimit = () => run(() => patch({ max_artworks: limit.trim() === "" ? null : Number(limit) }));
  const toggle = () => {
    const msg = a.is_active ? `¿Deshabilitar a ${a.display_name}? No podrá entrar y sus obras dejarán de verse.` : `¿Habilitar de nuevo a ${a.display_name}?`;
    if (window.confirm(msg)) run(() => patch({ is_active: !a.is_active }));
  };
  const reset = () => {
    if (window.confirm(`Se enviará un email a ${a.email} para que elija una contraseña nueva. ¿Continuar?`))
      run(() => authFetch(`/admin/artists/${a.id}/reset-password`, { method: "POST" }), "Email de restablecimiento enviado.");
  };

  return (
    <li className={`border border-line bg-white p-4 ${a.is_active ? "" : "opacity-70"}`}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-serif text-xl">
            {a.display_name}
            {a.is_admin && <span className="ml-2 align-middle text-[11px] uppercase tracking-wider text-gold">admin</span>}
          </p>
          <p className="truncate text-xs text-muted">{a.email}</p>
        </div>
        <p className="text-xs">
          {!a.is_active ? <span className="text-red-700">Deshabilitado</span> : !a.email_verified ? <span className="text-muted">Sin verificar</span> : <span className="text-gold">Activo</span>}
        </p>
      </div>

      <dl className="mt-3 grid grid-cols-4 gap-2 text-center">
        {[
          ["Obras", a.artworks_count],
          ["Publicadas", a.published_count],
          ["Contactos", a.inquiries_count],
          ["Visitas", a.visits_count],
        ].map(([k, v]) => (
          <div key={k}>
            <dd className="font-serif text-xl">{v}</dd>
            <dt className="text-[11px] text-muted">{k}</dt>
          </div>
        ))}
      </dl>

      {!a.is_admin && (
        <div className="mt-4 flex flex-wrap items-end gap-3 border-t border-line pt-3">
          <div>
            <label htmlFor={`lim-${a.id}`} className="mb-1 block text-[11px] text-muted">Límite de obras (vacío = sin límite)</label>
            <div className="flex gap-2">
              <input
                id={`lim-${a.id}`} inputMode="numeric" value={limit} onChange={(e) => setLimit(e.target.value.replace(/\D/g, ""))}
                className="min-h-11 w-24 rounded-md border border-line bg-white px-3 text-base md:text-sm"
              />
              <button disabled={busy} onClick={saveLimit} className="min-h-11 border border-line px-4 text-sm">Guardar</button>
            </div>
          </div>
          <button disabled={busy} onClick={reset} className="min-h-11 border border-line px-4 text-sm">Resetear contraseña</button>
          <button disabled={busy} onClick={toggle} className={`min-h-11 px-4 text-sm ${a.is_active ? "border border-red-700 text-red-700" : "bg-foreground text-background"}`}>
            {a.is_active ? "Deshabilitar" : "Habilitar"}
          </button>
        </div>
      )}
    </li>
  );
}

export default function AdminArtistas() {
  const { authFetch } = useSession();
  const [q, setQ] = useState("");
  const [data, setData] = useState<Page<AdminArtist> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      authFetch<Page<AdminArtist>>(`/admin/artists?page_size=50${q ? `&q=${encodeURIComponent(q)}` : ""}`)
        .then(setData)
        .catch(() => setError("No se han podido cargar los artistas.")),
    [authFetch, q],
  );
  useEffect(() => {
    const t = setTimeout(load, 250); // pequeña espera para no pedir en cada tecla
    return () => clearTimeout(t);
  }, [load]);

  return (
    <>
      <h1 className="font-serif text-3xl md:text-4xl">Artistas</h1>
      <p className="mt-1 text-sm text-muted">{data ? `${data.total} registrados` : "Cargando…"}</p>
      <div className="mt-4">
        <label htmlFor="q" className="sr-only">Buscar artista</label>
        <input
          id="q" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar por nombre o email"
          className="min-h-12 w-full rounded-md border border-line bg-white px-3 text-base outline-none focus:border-gold md:max-w-sm md:text-sm"
        />
      </div>
      {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
      {data?.items.length === 0 && <p className="mt-6 text-sm text-muted">No hay artistas que coincidan.</p>}
      <ul className="mt-6 space-y-4">
        {data?.items.map((a) => (
          <ArtistRow key={a.id} a={a} onChange={() => { setError(null); load(); }} onError={setError} />
        ))}
      </ul>
    </>
  );
}
