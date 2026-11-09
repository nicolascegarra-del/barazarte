import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { API_URL, formatPrice, formatSize } from "@/lib/api";
import { getArtwork, getNeighbors } from "@/lib/artworks-server";
import { ContactForm } from "@/components/ContactForm";
import { StatusBadge } from "@/components/StatusBadge";
import { VisitTracker } from "@/components/VisitTracker";
import { ArtworkViewer } from "@/components/artwork/ArtworkViewer";
import { ContactBar } from "@/components/artwork/ContactBar";
import { ShareButton } from "@/components/artwork/ShareButton";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

const priceLabel = (status: string, price: string | null) => (status === "vendido" ? "Vendida" : formatPrice(price));

/** Vista previa al compartir en WhatsApp, Instagram, Facebook…: foto de la obra, título, artista y precio. */
export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { id } = await params;
  const art = await getArtwork(id);
  if (!art) return { title: "Obra no encontrada · BarazArte" };
  const title = `${art.title} · ${art.artist.display_name}`;
  const description = `${art.technique} · ${formatSize(art)} · ${priceLabel(art.status, art.price)}. Obra original en BarazArte.`;
  const image = `${API_URL}/artworks/${art.id}/og.jpg`;
  return {
    title: `${title} · BarazArte`,
    description,
    alternates: { canonical: `/obras/${art.id}` },
    openGraph: {
      type: "article",
      title,
      description,
      url: `/obras/${art.id}`,
      images: [{ url: image, width: 1200, height: 630, alt: art.title, type: "image/jpeg" }],
    },
    twitter: { card: "summary_large_image", title, description, images: [image] },
  };
}

export default async function ObraPage({ params }: Params) {
  const { id } = await params;
  const [art, neighbors] = await Promise.all([getArtwork(id), getNeighbors(id)]);
  if (!art) notFound();
  const [main, ...rest] = art.images;
  const price = priceLabel(art.status, art.price);
  const canContact = art.status !== "vendido";

  return (
    <article className={`mx-auto grid max-w-6xl gap-10 px-4 py-8 md:grid-cols-2 md:px-8 md:py-12 ${canContact ? "pb-28 md:pb-12" : ""}`}>
      <VisitTracker artworkId={art.id} />
      <div className="w-full space-y-3">
        {main && (
          <ArtworkViewer
            src={main.url} alt={main.alt_text ?? art.title} width={main.width} height={main.height}
            badge={<StatusBadge status={art.status} />}
            prev={neighbors?.prev ?? null} next={neighbors?.next ?? null}
          />
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
          <p className="text-2xl">{price}</p>
          <StatusBadge status={art.status} className="border border-line shadow-none" />
        </div>
        <div className="mt-5">
          <ShareButton title={art.title} text={`${art.title}, de ${art.artist.display_name}, en BarazArte`} />
        </div>
        <div id="contacto" className="mt-8 scroll-mt-24">
          {!canContact ? (
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
      {canContact && <ContactBar price={price} targetId="contacto" />}
    </article>
  );
}
