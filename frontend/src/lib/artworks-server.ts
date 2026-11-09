import "server-only";
import { cache } from "react";
import { type ArtworkDetail, publicGet } from "./api";

/** Obra pública, compartida entre `generateMetadata` y la página en la misma petición (una sola llamada a la API). */
export const getArtwork = cache((id: string) => publicGet<ArtworkDetail>(`/artworks/${encodeURIComponent(id)}`));

/** Obra anterior y siguiente para navegar deslizando. */
export interface Neighbors { prev: { id: number; title: string } | null; next: { id: number; title: string } | null }
export const getNeighbors = cache((id: string) => publicGet<Neighbors>(`/artworks/${encodeURIComponent(id)}/neighbors`));
