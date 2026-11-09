import Link from "next/link";
import { type ArtworkListItem, formatPrice, formatSize } from "@/lib/api";
import { artworkPath } from "@/lib/slug";
import { StatusBadge } from "./StatusBadge";

/**
 * Obra en su "pared" con passe-partout: la rejilla es uniforme, pero el cuadro se muestra
 * entero y con su proporción real (nunca se recorta), con cartela de museo debajo.
 */
export function ArtworkCard({ art }: { art: ArtworkListItem }) {
  const sold = art.status === "vendido";
  return (
    <Link href={artworkPath(art.id, art.title)} className="group block">
      <div className="relative aspect-square bg-[#ece8e0] p-[12%] transition-colors duration-300 group-hover:bg-[#e6e1d7]">
        <div className="flex h-full w-full items-center justify-center">
          {art.cover_thumb_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={art.cover_thumb_url}
              alt={art.title}
              loading="lazy"
              className={`max-h-full max-w-full shadow-[0_6px_18px_rgba(0,0,0,.22)] transition-transform duration-300 group-hover:scale-[1.03] ${sold ? "opacity-90" : ""}`}
            />
          ) : (
            <span className="text-xs text-muted">Sin foto</span>
          )}
        </div>
        <StatusBadge status={art.status} className="absolute left-3 top-3" />
      </div>
      <div className="mt-4 border-t border-foreground pt-3">
        <h3 className="font-serif text-xl font-medium">{art.title}</h3>
        <p className="mt-1 text-xs leading-relaxed text-muted">
          {art.artist.display_name}
          <br />
          {art.technique} · {formatSize(art)} · {art.year}
        </p>
        <p className="mt-2 text-sm">
          {sold ? <span className="text-muted">Vendida</span> : formatPrice(art.price)}
          {art.status === "reservado" && <span className="ml-2 text-xs text-muted">· Reservada</span>}
        </p>
      </div>
    </Link>
  );
}
