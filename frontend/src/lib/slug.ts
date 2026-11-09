/** URLs legibles de las obras: `/obras/7-bosque-de-noche`. El número manda; el texto es para personas y buscadores. */

/** Texto en minúsculas, sin acentos ni signos, con guiones. */
export function slugify(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/ñ/g, "n")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60)
    .replace(/-+$/g, "");
}

/** Segmento de URL de una obra a partir de su id y su título. */
export const artworkSlug = (id: number, title: string) => {
  const s = slugify(title);
  return s ? `${id}-${s}` : String(id);
};

export const artworkPath = (id: number, title: string) => `/obras/${artworkSlug(id, title)}`;

/** decodeURIComponent que no lanza con secuencias mal formadas (p. ej. "%E0"): devuelve el texto tal cual. */
export function safeDecode(s: string): string {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

/** Id numérico al principio del segmento (`"7-bosque"` → 7). null si no empieza por un número. */
export function parseArtworkId(segment: string): number | null {
  const m = /^(\d+)(?:-|$)/.exec(safeDecode(segment));
  return m ? Number(m[1]) : null;
}
