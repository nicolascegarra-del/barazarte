import type { Metadata } from "next";
import Link from "next/link";
import { type ArtworkListItem, type Page, publicGet } from "@/lib/api";
import { activeCount, parseFilters, toApiQuery } from "@/lib/filters";
import { ArtworkGrid } from "@/components/ArtworkGrid";
import { ArtworkFilters, type Facets } from "@/components/ArtworkFilters";

export const dynamic = "force-dynamic";

type SP = { searchParams: Promise<Record<string, string | string[] | undefined>> };

/**
 * El catálogo completo se indexa con su canónica; las combinaciones de filtros no (serían cientos de
 * páginas casi duplicadas), aunque Google sigue sus enlaces hacia las obras.
 */
export async function generateMetadata({ searchParams }: SP): Promise<Metadata> {
  const filtered = activeCount(parseFilters(await searchParams)) > 0;
  return {
    title: "Obras de arte originales: cuadros a la venta · BarazArte",
    description:
      "Cuadros originales de artistas contemporáneos: óleo, acrílico, acuarela y técnica mixta. Filtra por precio, tamaño y técnica y contacta con el artista.",
    alternates: { canonical: "/obras" },
    robots: filtered ? { index: false, follow: true } : undefined,
  };
}

const EMPTY_FACETS: Facets = { techniques: [], artists: [], total: 0 };

export default async function Obras({ searchParams }: SP) {
  const filters = parseFilters(await searchParams);
  const [data, facets] = await Promise.all([
    publicGet<Page<ArtworkListItem>>(`/artworks?${toApiQuery(filters)}`),
    publicGet<Facets>("/artworks/facets"),
  ]);
  const filtered = activeCount(filters) > 0;

  return (
    <section className="mx-auto max-w-6xl px-4 py-10 md:px-8 md:py-12">
      <h1 className="font-serif text-4xl font-medium md:text-5xl">Obras</h1>
      {data && <p className="mt-2 text-sm text-muted">{data.total} {data.total === 1 ? "pieza" : "piezas"}{filtered ? " con estos filtros" : ""}.</p>}
      <div className="mt-6">
        <ArtworkFilters filters={filters} facets={facets ?? EMPTY_FACETS} />
      </div>
      <div className="mt-8">
        {data && data.items.length === 0 && filtered ? (
          <div className="py-10 text-sm text-muted">
            <p>No hay obras con estos filtros.</p>
            <Link href="/obras" className="mt-2 inline-block underline">Ver todas las obras</Link>
          </div>
        ) : (
          <ArtworkGrid data={data} />
        )}
      </div>
    </section>
  );
}
