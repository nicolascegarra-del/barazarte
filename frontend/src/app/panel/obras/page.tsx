"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { type ArtworkListItem, type ArtworkStatus, type Page, formatPrice, formatSize } from "@/lib/api";
import { useSession } from "@/lib/session";

const STATUSES: ArtworkStatus[] = ["borrador", "publicado", "reservado", "vendido"];

export default function MisObras() {
  const { authFetch } = useSession();
  const [arts, setArts] = useState<ArtworkListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () => authFetch<Page<ArtworkListItem>>("/panel/artworks?page_size=50").then((p) => setArts(p.items)).catch(() => setError("No se han podido cargar tus obras.")),
    [authFetch],
  );
  useEffect(() => { load(); }, [load]);

  async function setStatus(id: number, status: ArtworkStatus) {
    setError(null);
    try {
      await authFetch(`/panel/artworks/${id}`, { method: "PATCH", json: { status } });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cambiar el estado.");
    }
  }

  async function remove(a: ArtworkListItem) {
    if (!window.confirm(`¿Borrar «${a.title}» y sus fotos? No se puede deshacer.`)) return;
    try {
      await authFetch(`/panel/artworks/${a.id}`, { method: "DELETE" });
      await load();
    } catch {
      setError("No se pudo borrar la obra.");
    }
  }

  return (
    <>
      <h1 className="font-serif text-3xl md:text-4xl">Mis obras</h1>
      {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
      {arts === null && !error && <p className="mt-6 text-sm text-muted">Cargando…</p>}
      {arts?.length === 0 && <p className="mt-6 text-sm text-muted">Aún no tienes obras. <Link href="/panel/subir" className="underline">Sube la primera</Link>.</p>}
      <ul className="mt-6 divide-y divide-line border-y border-line empty:hidden">
        {arts?.map((a) => (
          <li key={a.id} className="flex flex-wrap items-center gap-3 py-3">
            <div className="h-16 w-14 shrink-0 bg-[#ece8e0]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {a.cover_thumb_url && <img src={a.cover_thumb_url} alt="" className="h-full w-full object-cover" />}
            </div>
            <div className="min-w-0 flex-1 basis-40">
              <Link href={`/panel/obras/${a.id}`} className="block truncate font-serif text-lg hover:underline">{a.title}</Link>
              <p className="text-xs text-muted">{formatSize(a)} · {formatPrice(a.price)}</p>
            </div>
            <select
              aria-label={`Estado de ${a.title}`} value={a.status} onChange={(e) => setStatus(a.id, e.target.value as ArtworkStatus)}
              className="min-h-11 rounded-md border border-line bg-white px-2 text-base md:text-sm"
            >
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </select>
            <Link href={`/panel/obras/${a.id}`} className="inline-flex min-h-11 items-center border border-line px-4 text-sm">Editar</Link>
            <button onClick={() => remove(a)} className="min-h-11 px-2 text-sm text-red-700 underline">Borrar</button>
          </li>
        ))}
      </ul>
    </>
  );
}
