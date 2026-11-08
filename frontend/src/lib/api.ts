/** Cliente de la API de BarazArte y tipos que reflejan los schemas del backend (FastAPI). */
export const API_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1`;

export type ArtworkStatus = "borrador" | "publicado" | "reservado" | "vendido";
export type InquiryStatus = "nueva" | "contactado" | "vendida";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
export interface ArtistSummary { id: number; display_name: string }
export interface ArtworkImage { id: number; url: string; thumb_url: string; alt_text: string | null; position: number; width: number; height: number }
// Decimal se serializa como string en JSON.
export interface ArtworkListItem {
  id: number; title: string; technique: string; width_cm: string; height_cm: string; year: number;
  price: string | null; status: ArtworkStatus; artist: ArtistSummary; cover_thumb_url: string | null;
}
export interface ArtworkDetail extends Omit<ArtworkListItem, "cover_thumb_url"> {
  depth_cm: string | null; description: string | null; images: ArtworkImage[];
}
export interface Inquiry {
  id: number; artwork_id: number | null; artwork_title: string; name: string; email: string;
  phone: string | null; message: string; status: InquiryStatus; created_at: string;
}

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

/** Convierte una respuesta no válida en ApiError usando el formato de error estándar Klyp. */
export async function parseResponse<T>(res: Response): Promise<T> {
  if (res.ok) return (res.status === 204 ? undefined : await res.json()) as T;
  let code = "ERROR";
  let message = "Algo ha fallado. Inténtalo de nuevo.";
  try {
    const body = await res.json();
    code = body?.error?.code ?? code;
    message = body?.error?.message ?? message;
  } catch {
    /* respuesta sin JSON */
  }
  throw new ApiError(res.status, code, message);
}

/** GET público desde el servidor. Devuelve null si la API no responde o da error (la página muestra un aviso). */
export async function publicGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    return res.ok ? ((await res.json()) as T) : null;
  } catch {
    return null;
  }
}

const num = (s: string) => Number(s).toLocaleString("es-ES", { maximumFractionDigits: 2 });
export const formatSize = (a: { width_cm: string; height_cm: string }) => `${num(a.width_cm)} × ${num(a.height_cm)} cm`;
export const formatPrice = (p: string | null) =>
  p === null
    ? "Consultar precio"
    : new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(Number(p));
