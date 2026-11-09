import type { ArtworkStatus } from "@/lib/api";

// Convención de galería: punto rojo = vendida, punto ámbar = reservada.
const STYLES: Partial<Record<ArtworkStatus, { label: string; dot: string }>> = {
  vendido: { label: "Vendida", dot: "bg-[#b3261e]" },
  reservado: { label: "Reservada", dot: "bg-[#d29a1d]" },
};

/** Etiqueta de estado de la obra; no muestra nada si está disponible. */
export function StatusBadge({ status, className = "" }: { status: ArtworkStatus; className?: string }) {
  const s = STYLES[status];
  if (!s) return null;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full bg-white/95 px-2.5 py-1 text-[11px] font-medium text-foreground shadow-sm ${className}`}>
      <span className={`h-2 w-2 rounded-full ${s.dot}`} aria-hidden />
      {s.label}
    </span>
  );
}
