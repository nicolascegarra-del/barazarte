import type { ArtworkListItem, Page } from "@/lib/api";
import { ArtworkCard } from "./ArtworkCard";

/** Rejilla de obras con los estados vacío y error que exige el estándar. */
export function ArtworkGrid({ data }: { data: Page<ArtworkListItem> | null }) {
  if (!data) return <p className="py-10 text-sm text-muted">No se han podido cargar las obras. Inténtalo en unos minutos.</p>;
  if (data.items.length === 0) return <p className="py-10 text-sm text-muted">Todavía no hay obras publicadas.</p>;
  return (
    <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3 lg:gap-10">
      {data.items.map((a) => (
        <ArtworkCard key={a.id} art={a} />
      ))}
    </div>
  );
}
