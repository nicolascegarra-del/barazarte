"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { type Inquiry, type InquiryStatus, type Page } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useUnread } from "@/lib/unread";
import { PushToggle } from "@/components/panel/PushToggle";

const STATUSES: InquiryStatus[] = ["nueva", "contactado", "vendida"];

export default function Consultas() {
  const { authFetch } = useSession();
  const { markAllRead } = useUnread();
  const [items, setItems] = useState<Inquiry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Las que llegaron sin leer se siguen resaltando mientras el artista está en la página.
  const [fresh, setFresh] = useState<Set<number>>(new Set());
  const marked = useRef(false);

  const load = useCallback(async () => {
    try {
      const p = await authFetch<Page<Inquiry>>("/panel/inquiries?page_size=50");
      setItems(p.items);
      const unread = p.items.filter((q) => !q.read_at).map((q) => q.id);
      if (unread.length) setFresh((prev) => new Set([...prev, ...unread]));
      // Al abrir la página se dan por leídas (una sola vez por visita).
      if (unread.length && !marked.current) {
        marked.current = true;
        void markAllRead();
      }
    } catch {
      setError("No se han podido cargar las consultas.");
    }
  }, [authFetch, markAllRead]);
  useEffect(() => { void load(); }, [load]);

  async function setStatus(id: number, status: InquiryStatus) {
    try {
      await authFetch(`/panel/inquiries/${id}`, { method: "PATCH", json: { status } });
      await load();
    } catch {
      setError("No se pudo actualizar la consulta.");
    }
  }

  return (
    <>
      <h1 className="font-serif text-3xl md:text-4xl">Consultas</h1>
      <p className="mt-1 text-sm text-muted">Personas interesadas en tus obras. También te llegan por email.</p>
      <div className="mt-5"><PushToggle /></div>
      {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
      {items === null && !error && <p className="mt-6 text-sm text-muted">Cargando…</p>}
      {items?.length === 0 && <p className="mt-6 text-sm text-muted">Todavía no has recibido consultas.</p>}
      <ul className="mt-6 space-y-4">
        {items?.map((q) => {
          const isNew = fresh.has(q.id);
          return (
            <li key={q.id} className={`border bg-white p-4 ${isNew ? "border-gold border-l-4" : "border-line"}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="flex items-center gap-2 font-serif text-lg">
                    {q.artwork_title}
                    {isNew && <span className="rounded-full bg-[#b3261e] px-2 py-0.5 font-sans text-[10px] font-semibold uppercase tracking-wider text-white">Nueva</span>}
                  </p>
                  <p className="text-xs text-muted">{new Date(q.created_at).toLocaleString("es-ES", { dateStyle: "short", timeStyle: "short" })}</p>
                </div>
                <select
                  aria-label={`Estado de la consulta de ${q.name}`} value={q.status} onChange={(e) => setStatus(q.id, e.target.value as InquiryStatus)}
                  className="min-h-11 rounded-md border border-line bg-white px-2 text-base md:text-sm"
                >
                  {STATUSES.map((s) => <option key={s}>{s}</option>)}
                </select>
              </div>
              <p className="mt-3 whitespace-pre-line text-sm">{q.message}</p>
              <p className="mt-3 text-sm">
                {q.name} · <a className="underline" href={`mailto:${q.email}`}>{q.email}</a>
                {q.phone && <> · <a className="underline" href={`tel:${q.phone}`}>{q.phone}</a></>}
              </p>
            </li>
          );
        })}
      </ul>
    </>
  );
}
