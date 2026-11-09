import { notFound } from "next/navigation";
import { type ArtworkDetail, formatPrice, formatSize, publicGet } from "@/lib/api";
import { ContactForm } from "@/components/ContactForm";
import { StatusBadge } from "@/components/StatusBadge";
import { VisitTracker } from "@/components/VisitTracker";

export const dynamic = "force-dynamic";

export default async function ObraPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const art = await publicGet<ArtworkDetail>(`/artworks/${encodeURIComponent(id)}`);
  if (!art) notFound();
  const [main, ...rest] = art.images;

  return (
    <article className="mx-auto grid max-w-6xl gap-10 px-4 py-12 md:grid-cols-2 md:px-8">
      <VisitTracker artworkId={art.id} />
      <div className="w-full space-y-3">
        {main && (
          <div className="relative flex items-center justify-center bg-[#ece8e0] p-[8%]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={main.url} alt={main.alt_text ?? art.title} width={main.width} height={main.height}
              className="h-auto max-h-[70vh] w-auto max-w-full shadow-[0_10px_28px_rgba(0,0,0,.25)]"
            />
            <StatusBadge status={art.status} className="absolute left-3 top-3" />
          </div>
        )}
        {rest.length > 0 && (
          <div className="grid grid-cols-3 gap-3">
            {rest.map((im) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={im.id} src={im.thumb_url} alt={im.alt_text ?? `Detalle de ${art.title}`} loading="lazy" className="h-auto w-full" />
            ))}
          </div>
        )}
      </div>
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-muted">{art.artist.display_name}</p>
        <h1 className="mt-2 font-serif text-4xl font-medium md:text-5xl">{art.title}</h1>
        <div className="mt-5 border-t border-foreground pt-3 text-sm text-muted">
          {art.technique} · {formatSize(art)} · {art.year}
        </div>
        {art.description && <p className="mt-4 whitespace-pre-line text-sm leading-7">{art.description}</p>}
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <p className="text-2xl">{art.status === "vendido" ? "Vendida" : formatPrice(art.price)}</p>
          <StatusBadge status={art.status} className="border border-line shadow-none" />
        </div>
        <div className="mt-8">
          {art.status === "vendido" ? (
            <p className="text-sm text-muted">Esta obra ya ha encontrado hogar.</p>
          ) : (
            <>
              {art.status === "reservado" && (
                <p className="mb-4 border-l-2 border-[#d29a1d] pl-3 text-sm text-muted">
                  Esta obra está reservada. Puedes escribir al artista por si vuelve a quedar disponible.
                </p>
              )}
              <ContactForm artworkId={art.id} title={art.title} />
            </>
          )}
        </div>
      </div>
    </article>
  );
}
