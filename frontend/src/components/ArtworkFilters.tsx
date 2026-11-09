"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { SlidersHorizontal, X } from "lucide-react";
import { type Filters, PRICE_RANGES, SIZES, SORTS, activeCount, toHref } from "@/lib/filters";

export interface Facets {
  techniques: { name: string; count: number }[];
  artists: { id: number; display_name: string; count: number }[];
  total: number;
}

const select = "min-h-11 rounded-md border border-line bg-white px-3 text-sm outline-none focus:border-gold";

function Chip({ on, children, onClick }: { on: boolean; children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      type="button" aria-pressed={on} onClick={onClick}
      className={`min-h-11 rounded-full border px-4 text-sm ${on ? "border-foreground bg-foreground text-background" : "border-line bg-white"}`}
    >
      {children}
    </button>
  );
}

/** Etiquetas legibles de los filtros activos, para mostrarlas como chips que se pueden quitar. */
function labels(f: Filters, facets: Facets): { key: keyof Filters; label: string }[] {
  const out: { key: keyof Filters; label: string }[] = [];
  if (f.tecnica) out.push({ key: "tecnica", label: f.tecnica });
  if (f.precio) out.push({ key: "precio", label: PRICE_RANGES.find((r) => r.value === f.precio)?.label ?? f.precio });
  if (f.tamano) out.push({ key: "tamano", label: SIZES.find((s) => s.value === f.tamano)?.label ?? f.tamano });
  if (f.artista) out.push({ key: "artista", label: facets.artists.find((a) => String(a.id) === f.artista)?.display_name ?? "Artista" });
  if (f.disponibles) out.push({ key: "disponibles", label: "Solo disponibles" });
  return out;
}

/**
 * Filtros del catálogo. Escritorio: barra con desplegables que aplica al momento.
 * Móvil: botón "Filtros" que abre un panel inferior con botones grandes y se aplica con "Ver obras".
 */
export function ArtworkFilters({ filters, facets }: { filters: Filters; facets: Facets }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [sheet, setSheet] = useState(false);
  const [draft, setDraft] = useState<Filters>(filters);

  useEffect(() => setDraft(filters), [filters]);
  useEffect(() => {
    document.body.style.overflow = sheet ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [sheet]);

  const go = (f: Filters) => start(() => router.push(toHref(f), { scroll: false }));
  const set = (k: keyof Filters, v: string | undefined) => go({ ...filters, [k]: v || undefined });
  const toggle = (k: keyof Filters, v: string) => setDraft((d) => ({ ...d, [k]: d[k] === v ? undefined : v }));
  const n = activeCount(filters);
  const active = labels(filters, facets);

  return (
    <div className={pending ? "opacity-60 transition-opacity" : ""} aria-busy={pending}>
      {/* Escritorio */}
      <div className="hidden flex-wrap items-center gap-3 md:flex">
        <select aria-label="Técnica" className={select} value={filters.tecnica ?? ""} onChange={(e) => set("tecnica", e.target.value)}>
          <option value="">Todas las técnicas</option>
          {facets.techniques.map((t) => <option key={t.name} value={t.name}>{t.name} ({t.count})</option>)}
        </select>
        <select aria-label="Precio" className={select} value={filters.precio ?? ""} onChange={(e) => set("precio", e.target.value)}>
          <option value="">Cualquier precio</option>
          {PRICE_RANGES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
        <select aria-label="Tamaño" className={select} value={filters.tamano ?? ""} onChange={(e) => set("tamano", e.target.value)}>
          <option value="">Cualquier tamaño</option>
          {SIZES.map((s) => <option key={s.value} value={s.value}>{s.label} ({s.hint})</option>)}
        </select>
        {facets.artists.length > 1 && (
          <select aria-label="Artista" className={select} value={filters.artista ?? ""} onChange={(e) => set("artista", e.target.value)}>
            <option value="">Todos los artistas</option>
            {facets.artists.map((a) => <option key={a.id} value={a.id}>{a.display_name} ({a.count})</option>)}
          </select>
        )}
        <label className="flex min-h-11 items-center gap-2 text-sm">
          <input type="checkbox" className="h-5 w-5 accent-[#8a6d2f]" checked={!!filters.disponibles} onChange={(e) => set("disponibles", e.target.checked ? "1" : undefined)} />
          Solo disponibles
        </label>
        <select aria-label="Ordenar" className={`${select} ml-auto`} value={filters.orden ?? "recientes"} onChange={(e) => set("orden", e.target.value === "recientes" ? undefined : e.target.value)}>
          {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      {/* Móvil */}
      <div className="flex gap-3 md:hidden">
        <button type="button" onClick={() => setSheet(true)} className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 border border-foreground text-sm">
          <SlidersHorizontal size={16} aria-hidden /> Filtros{n > 0 && ` (${n})`}
        </button>
        <select aria-label="Ordenar" className={`${select} flex-1`} value={filters.orden ?? "recientes"} onChange={(e) => set("orden", e.target.value === "recientes" ? undefined : e.target.value)}>
          {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      {active.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {active.map((a) => (
            <button key={a.key} type="button" onClick={() => set(a.key, undefined)} aria-label={`Quitar filtro ${a.label}`}
              className="inline-flex min-h-9 items-center gap-1.5 rounded-full bg-[#ece8e0] px-3 text-xs">
              {a.label} <X size={14} aria-hidden />
            </button>
          ))}
          <button type="button" onClick={() => go({ orden: filters.orden })} className="min-h-9 px-2 text-xs text-muted underline">Limpiar filtros</button>
        </div>
      )}

      {sheet && (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="Filtros">
          <button type="button" aria-label="Cerrar filtros" className="absolute inset-0 bg-black/40" onClick={() => setSheet(false)} />
          <div className="absolute inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-2xl bg-background px-4 pb-[calc(env(safe-area-inset-bottom)+16px)] pt-3">
            <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-line" aria-hidden />
            <div className="flex items-center justify-between">
              <h2 className="font-serif text-2xl">Filtros</h2>
              <button type="button" onClick={() => setSheet(false)} aria-label="Cerrar" className="flex h-11 w-11 items-center justify-center"><X size={22} aria-hidden /></button>
            </div>

            <fieldset className="mt-4">
              <legend className="mb-2 text-xs uppercase tracking-wider text-muted">Precio</legend>
              <div className="flex flex-wrap gap-2">{PRICE_RANGES.map((r) => <Chip key={r.value} on={draft.precio === r.value} onClick={() => toggle("precio", r.value)}>{r.label}</Chip>)}</div>
            </fieldset>
            <fieldset className="mt-5">
              <legend className="mb-2 text-xs uppercase tracking-wider text-muted">Tamaño</legend>
              <div className="flex flex-wrap gap-2">{SIZES.map((s) => <Chip key={s.value} on={draft.tamano === s.value} onClick={() => toggle("tamano", s.value)}>{s.label} <span className="opacity-70">· {s.hint}</span></Chip>)}</div>
            </fieldset>
            {facets.techniques.length > 0 && (
              <fieldset className="mt-5">
                <legend className="mb-2 text-xs uppercase tracking-wider text-muted">Técnica</legend>
                <div className="flex flex-wrap gap-2">{facets.techniques.map((t) => <Chip key={t.name} on={draft.tecnica === t.name} onClick={() => toggle("tecnica", t.name)}>{t.name}</Chip>)}</div>
              </fieldset>
            )}
            {facets.artists.length > 1 && (
              <fieldset className="mt-5">
                <legend className="mb-2 text-xs uppercase tracking-wider text-muted">Artista</legend>
                <div className="flex flex-wrap gap-2">{facets.artists.map((a) => <Chip key={a.id} on={draft.artista === String(a.id)} onClick={() => toggle("artista", String(a.id))}>{a.display_name}</Chip>)}</div>
              </fieldset>
            )}
            <label className="mt-5 flex min-h-12 items-center gap-3 text-sm">
              <input type="checkbox" className="h-5 w-5 accent-[#8a6d2f]" checked={!!draft.disponibles} onChange={(e) => setDraft((d) => ({ ...d, disponibles: e.target.checked ? "1" : undefined }))} />
              Solo obras disponibles (sin reservadas ni vendidas)
            </label>

            <div className="sticky bottom-0 mt-6 flex gap-3 bg-background pt-3">
              <button type="button" onClick={() => setDraft({ orden: draft.orden })} className="min-h-12 flex-1 border border-line text-sm">Limpiar</button>
              <button type="button" onClick={() => { setSheet(false); go(draft); }} className="min-h-12 flex-[2] bg-foreground text-xs uppercase tracking-[0.18em] text-background">Ver obras</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
