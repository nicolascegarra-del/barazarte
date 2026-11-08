"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { type AdminStats } from "@/lib/api";
import { useSession } from "@/lib/session";

function Stat({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <div className="border border-line bg-white p-4">
      <dd className="font-serif text-3xl">{value.toLocaleString("es-ES")}</dd>
      <dt className="text-xs text-muted">{label}</dt>
      {hint && <p className="mt-1 text-[11px] text-muted">{hint}</p>}
    </div>
  );
}

/** Barras de visitas de los últimos 30 días (SVG sencillo, sin librería de gráficos). */
function VisitsChart({ data }: { data: { date: string; count: number }[] }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <figure>
      <svg viewBox={`0 0 ${data.length * 10} 60`} role="img" aria-label="Visitas por día en los últimos 30 días" className="h-32 w-full" preserveAspectRatio="none">
        {data.map((d, i) => {
          const h = (d.count / max) * 56;
          return (
            <rect key={d.date} x={i * 10 + 1} y={58 - h} width={8} height={Math.max(h, 0.6)} fill="#8a6d2f">
              <title>{`${d.date}: ${d.count}`}</title>
            </rect>
          );
        })}
      </svg>
      <figcaption className="mt-1 flex justify-between text-[11px] text-muted">
        <span>{data[0]?.date}</span>
        <span>{data.at(-1)?.date}</span>
      </figcaption>
    </figure>
  );
}

export default function AdminHome() {
  const { authFetch } = useSession();
  const [s, setS] = useState<AdminStats | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    authFetch<AdminStats>("/admin/stats").then(setS).catch(() => setError(true));
  }, [authFetch]);

  return (
    <>
      <h1 className="font-serif text-3xl md:text-4xl">Administración</h1>
      <p className="mt-1 text-sm text-muted">Visión general de BarazArte.</p>
      {error && <p role="alert" className="mt-6 text-sm text-red-700">No se han podido cargar las estadísticas.</p>}
      {!s && !error && <p className="mt-6 text-sm text-muted">Cargando…</p>}
      {s && (
        <div className="mt-6 space-y-8">
          <section aria-labelledby="h-art">
            <h2 id="h-art" className="font-serif text-2xl">Artistas</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Stat label="Registrados" value={s.artists.total} />
              <Stat label="Activos" value={s.artists.active} />
              <Stat label="Deshabilitados" value={s.artists.disabled} />
              <Stat label="Sin verificar email" value={s.artists.unverified} />
            </dl>
            <div className="mt-3 flex flex-wrap gap-x-6">
              <Link href="/admin/artistas" className="inline-flex min-h-11 items-center text-sm underline">Gestionar artistas</Link>
              <Link href="/admin/correo" className="inline-flex min-h-11 items-center text-sm underline">Configurar correo de la plataforma</Link>
            </div>
          </section>

          <section aria-labelledby="h-con">
            <h2 id="h-con" className="font-serif text-2xl">Contactos con artistas</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Stat label="Formularios enviados" value={s.inquiries.total} hint="Personas que han escrito a un artista" />
              <Stat label="Nuevos" value={s.inquiries.nueva} />
              <Stat label="Contactados" value={s.inquiries.contactado} />
              <Stat label="Vendidas" value={s.inquiries.vendida} />
            </dl>
          </section>

          <section aria-labelledby="h-obr">
            <h2 id="h-obr" className="font-serif text-2xl">Obras</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-5">
              <Stat label="Total" value={s.artworks.total} />
              <Stat label="Publicadas" value={s.artworks.publicado} />
              <Stat label="Borradores" value={s.artworks.borrador} />
              <Stat label="Reservadas" value={s.artworks.reservado} />
              <Stat label="Vendidas" value={s.artworks.vendido} />
            </dl>
          </section>

          <section aria-labelledby="h-vis">
            <h2 id="h-vis" className="font-serif text-2xl">Visitas a la web</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3">
              <Stat label="Últimos 30 días" value={s.visits.last_30_days} />
              <Stat label="Total" value={s.visits.total} hint="Sin cookies ni datos personales" />
            </dl>
            <div className="mt-4 border border-line bg-white p-4">
              <VisitsChart data={s.visits.by_day} />
            </div>
          </section>
        </div>
      )}
    </>
  );
}
