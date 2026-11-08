import Link from "next/link";
import { type ArtworkListItem, formatPrice, formatSize } from "@/lib/api";

/** Obra con cartela de museo: título, técnica, medidas y precio. */
export function ArtworkCard({ art }: { art: ArtworkListItem }) {
  return (
    <Link href={`/obras/${art.id}`} className="group block">
      <div className="flex aspect-[4/5] items-center justify-center bg-[#ece8e0] shadow-md transition-transform duration-300 group-hover:scale-[1.02]">
        {art.cover_thumb_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={art.cover_thumb_url} alt={art.title} loading="lazy" className="h-full w-full object-cover" />
        ) : (
          <span className="text-xs text-muted">Sin foto</span>
        )}
      </div>
      <div className="mt-4 border-t border-foreground pt-3">
        <h3 className="font-serif text-xl font-medium">{art.title}</h3>
        <p className="mt-1 text-xs leading-relaxed text-muted">
          {art.technique}
          <br />
          {formatSize(art)} · {art.year}
        </p>
        <p className="mt-2 text-sm">{art.status === "vendido" ? "Vendido" : formatPrice(art.price)}</p>
      </div>
    </Link>
  );
}
