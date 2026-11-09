"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { type ArtworkListItem, type Inquiry, type Page, formatPrice, formatSize } from "@/lib/api";
import { useSession } from "@/lib/session";

export default function PanelHome() {
  const { artist, authFetch } = useSession();
  const [arts, setArts] = useState<Page<ArtworkListItem> | null>(null);
  const [inq, setInq] = useState<Page<Inquiry> | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([
      authFetch<Page<ArtworkListItem>>("/panel/artworks?page_size=50"),
      authFetch<Page<Inquiry>>("/panel/inquiries?page_size=50"),
    ])
      .then(([a, i]) => { setArts(a); setInq(i); })
      .catch(() => setError(true));
  }, [authFetch]);

  const count = (s: string) => arts?.items.filter((a) => a.status === s).length ?? 0;
  const stats = [
    { label: "Publicadas", value: count("publicado") },
    { label: "Vendidas", value: count("vendido") },
    { label: "Consultas nuevas", value: inq?.items.filter((i) => i.status === "nueva").length ?? 0 },
  ];

  return (
    <>
      <h1 className="font-serif text-3xl md:text-4xl">Hola, {artist?.display_name}</h1>
      <p className="mt-1 text-sm text-muted">
        Este es el resumen de tu galería.
        {artist && (
          <>
            {" "}
            {artist.max_artworks === null
              ? `Tienes ${artist.artworks_count} obras.`
              : `Has usado ${artist.artworks_count} de ${artist.max_artworks} obras.`}
          </>
        )}
      </p>

      <Link
        href="/panel/subir"
        className="mt-6 flex min-h-16 items-center justify-center gap-3 bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background hover:bg-gold md:inline-flex"
      >
        <Plus size={18} aria-hidden /> Subir una obra nueva
      </Link>

      {error && <p role="alert" className="mt-6 text-sm text-red-700">No se han podido cargar tus datos.</p>}

      <dl className="mt-8 grid grid-cols-3 gap-3">
        {stats.map((s) => (
          <div key={s.label} className="border border-line bg-white p-3 md:p-5">
            <dd className="font-serif text-3xl">{s.value}</dd>
            <dt className="text-xs text-muted">{s.label}</dt>
          </div>
        ))}
      </dl>

      <h2 className="mt-10 font-serif text-2xl">Tus obras</h2>
      {arts && arts.items.length === 0 && (
        <p className="mt-4 text-sm text-muted">Aún no has subido ninguna obra. Pulsa «Subir una obra nueva» para empezar.</p>
      )}
      <ul className="mt-4 divide-y divide-line border-y border-line empty:hidden">
        {arts?.items.map((a) => (
          <li key={a.id} className="flex items-center gap-4 py-3">
            <div className="h-16 w-14 shrink-0 bg-[#ece8e0]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {a.cover_thumb_url && <img src={a.cover_thumb_url} alt="" className="h-full w-full object-cover" />}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate font-serif text-lg">{a.title}</p>
              <p className="text-xs text-muted">{formatSize(a)} · {formatPrice(a.price)} · {a.status}</p>
            </div>
            <Link href={`/panel/obras/${a.id}`} className="min-h-11 content-center px-2 text-sm underline">Editar</Link>
          </li>
        ))}
      </ul>
    </>
  );
}
