import type { MetadataRoute } from "next";
import { type ArtworkListItem, type Page, publicGet } from "@/lib/api";
import { SITE_URL } from "@/lib/seo";
import { artworkPath } from "@/lib/slug";

// Se regenera como mucho cada hora: las obras nuevas aparecen sin redesplegar.
export const revalidate = 3600;

const PAGE_SIZE = 50;
const MAX_PAGES = 40; // hasta 2.000 obras; de sobra para una galería

/** Todas las obras visibles (publicadas, reservadas y vendidas) recorriendo la paginación de la API. */
async function allArtworks(): Promise<ArtworkListItem[]> {
  const items: ArtworkListItem[] = [];
  for (let page = 1; page <= MAX_PAGES; page++) {
    const data = await publicGet<Page<ArtworkListItem>>(`/artworks?page=${page}&page_size=${PAGE_SIZE}`);
    if (!data) break;
    items.push(...data.items);
    if (page >= data.pages) break;
  }
  return items;
}

/** Mapa del sitio para Google: páginas públicas y una entrada por obra. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const artworks = await allArtworks();
  const statics: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, changeFrequency: "daily", priority: 1 },
    { url: `${SITE_URL}/obras`, changeFrequency: "daily", priority: 0.9 },
    { url: `${SITE_URL}/registro`, changeFrequency: "monthly", priority: 0.4 },
    { url: `${SITE_URL}/legal/aviso-legal`, changeFrequency: "yearly", priority: 0.1 },
    { url: `${SITE_URL}/legal/privacidad`, changeFrequency: "yearly", priority: 0.1 },
    { url: `${SITE_URL}/legal/cookies`, changeFrequency: "yearly", priority: 0.1 },
  ];
  return [
    ...statics,
    ...artworks.map((a) => ({
      url: `${SITE_URL}${artworkPath(a.id, a.title)}`,
      changeFrequency: "weekly" as const,
      // Las vendidas siguen visibles (historial del artista) pero con menos prioridad.
      priority: a.status === "vendido" ? 0.4 : 0.8,
      images: a.cover_thumb_url ? [a.cover_thumb_url] : undefined,
    })),
  ];
}
