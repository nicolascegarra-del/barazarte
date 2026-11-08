"use client";

import { useCallback, useEffect, useState } from "react";
import { type Inquiry, type InquiryStatus, type Page } from "@/lib/api";
import { useSession } from "@/lib/session";

const STATUSES: InquiryStatus[] = ["nueva", "contactado", "vendida"];

export default function Consultas() {
  const { authFetch } = useSession();
  const [items, setItems] = useState<Inquiry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () => authFetch<Page<Inquiry>>("/panel/inquiries?page_size=50").then((p) => setItems(p.items)).catch(() => setError("No se han podido cargar las consultas.")),
    [authFetch],
  );
  useEffect(() => { load(); }, [load]);

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
      {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
      {items?.length === 0 && <p className="mt-6 text-sm text-muted">Todavía no has recibido consultas.</p>}
      <ul className="mt-6 space-y-4">
        {items?.map((q) => (
          <li key={q.id} className="border border-line bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-serif text-lg">{q.artwork_title}</p>
                <p className="text-xs text-muted">{new Date(q.created_at).toLocaleDateString("es-ES")}</p>
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
        ))}
      </ul>
    </>
  );
}
