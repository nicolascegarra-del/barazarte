/** Filtros del catálogo: parámetros de la URL (en español, compartibles) ↔ parámetros de la API. */
export interface Filters {
  tecnica?: string;
  precio?: string; // "0-500" | "500-1000" | "1000-2000" | "2000-"
  tamano?: string; // "pequeno" | "mediano" | "grande"
  artista?: string;
  disponibles?: string; // "1"
  orden?: string; // "recientes" | "precio_asc" | "precio_desc"
}

export const PRICE_RANGES = [
  { value: "0-500", label: "Hasta 500 €" },
  { value: "500-1000", label: "500 – 1.000 €" },
  { value: "1000-2000", label: "1.000 – 2.000 €" },
  { value: "2000-", label: "Más de 2.000 €" },
];
export const SIZES = [
  { value: "pequeno", label: "Pequeño", hint: "menos de 50 cm" },
  { value: "mediano", label: "Mediano", hint: "50 – 100 cm" },
  { value: "grande", label: "Grande", hint: "más de 100 cm" },
];
export const SORTS = [
  { value: "recientes", label: "Más recientes" },
  { value: "precio_asc", label: "Precio: de menor a mayor" },
  { value: "precio_desc", label: "Precio: de mayor a menor" },
];

const KEYS: (keyof Filters)[] = ["tecnica", "precio", "tamano", "artista", "disponibles", "orden"];

/** Lee y valida los filtros de la URL (ignora valores desconocidos). */
export function parseFilters(sp: Record<string, string | string[] | undefined>): Filters {
  const f: Filters = {};
  for (const k of KEYS) {
    const v = sp[k];
    if (typeof v === "string" && v.trim()) f[k] = v.trim();
  }
  if (f.precio && !PRICE_RANGES.some((r) => r.value === f.precio)) delete f.precio;
  if (f.tamano && !SIZES.some((s) => s.value === f.tamano)) delete f.tamano;
  if (f.orden && !SORTS.some((s) => s.value === f.orden)) delete f.orden;
  if (f.artista && !/^\d+$/.test(f.artista)) delete f.artista;
  if (f.disponibles && f.disponibles !== "1") delete f.disponibles;
  return f;
}

/** Construye la consulta para GET /artworks. */
export function toApiQuery(f: Filters, pageSize = 48): string {
  const q = new URLSearchParams({ page_size: String(pageSize) });
  if (f.tecnica) q.set("technique", f.tecnica);
  if (f.precio) {
    const [min, max] = f.precio.split("-");
    if (min) q.set("min_price", min);
    if (max) q.set("max_price", max);
  }
  if (f.tamano) q.set("size", f.tamano);
  if (f.artista) q.set("artist_id", f.artista);
  if (f.disponibles) q.set("available", "true");
  if (f.orden) q.set("sort", f.orden);
  return q.toString();
}

/** URL del catálogo con estos filtros (sin parámetros vacíos). */
export function toHref(f: Filters): string {
  const q = new URLSearchParams();
  for (const k of KEYS) if (f[k]) q.set(k, f[k]!);
  const s = q.toString();
  return s ? `/obras?${s}` : "/obras";
}

/** Número de filtros activos (el orden no cuenta como filtro). */
export const activeCount = (f: Filters) => KEYS.filter((k) => k !== "orden" && f[k]).length;
