import { type ArtworkDetail, API_URL } from "./api";
import { artworkPath } from "./slug";

/** URL pública de la web (dominio de producción). Se lee en ejecución desde SITE_URL. */
export const SITE_URL = (process.env.SITE_URL ?? "http://localhost:3000").replace(/\/+$/, "");
export const SITE_NAME = "BarazArte";
export const SITE_DESCRIPTION =
  "BarazArte es una galería de arte online con cuadros originales de artistas contemporáneos. Descubre óleos, acrílicos y acuarelas y contacta directamente con el artista.";

/** La galería y la web: ayuda a que Google muestre la marca al buscar «BarazArte». */
export function siteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "ArtGallery",
        "@id": `${SITE_URL}/#galeria`,
        name: SITE_NAME,
        url: SITE_URL,
        logo: `${SITE_URL}/icons/icon-512.png`,
        image: `${SITE_URL}/icons/icon-512.png`,
        description: SITE_DESCRIPTION,
      },
      {
        "@type": "WebSite",
        "@id": `${SITE_URL}/#web`,
        name: SITE_NAME,
        url: SITE_URL,
        inLanguage: "es-ES",
        publisher: { "@id": `${SITE_URL}/#galeria` },
      },
    ],
  };
}

const AVAILABILITY: Record<string, string> = {
  publicado: "https://schema.org/InStock",
  reservado: "https://schema.org/LimitedAvailability",
  vendido: "https://schema.org/SoldOut",
};

/** Obra de arte con autor, técnica, medidas y, si tiene precio, oferta en euros. */
export function artworkJsonLd(art: ArtworkDetail) {
  const url = `${SITE_URL}${artworkPath(art.id, art.title)}`;
  const data: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "VisualArtwork",
    name: art.title,
    url,
    image: [art.images[0]?.url, `${API_URL}/artworks/${art.id}/og.jpg`].filter(Boolean),
    description: art.description || `${art.title}, obra original de ${art.artist.display_name}.`,
    creator: { "@type": "Person", name: art.artist.display_name },
    artMedium: art.technique,
    artform: "Pintura",
    dateCreated: String(art.year),
    width: { "@type": "Distance", name: `${Number(art.width_cm)} cm` },
    height: { "@type": "Distance", name: `${Number(art.height_cm)} cm` },
    inLanguage: "es-ES",
    isPartOf: { "@id": `${SITE_URL}/#galeria` },
  };
  if (art.price !== null) {
    data.offers = {
      "@type": "Offer",
      price: Number(art.price).toFixed(2),
      priceCurrency: "EUR",
      availability: AVAILABILITY[art.status] ?? "https://schema.org/InStock",
      url,
      seller: { "@id": `${SITE_URL}/#galeria` },
    };
  }
  return data;
}
