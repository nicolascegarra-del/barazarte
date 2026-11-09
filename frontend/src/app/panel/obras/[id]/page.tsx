"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, ExternalLink, ImagePlus } from "lucide-react";
import { type ArtworkDetail, type ArtworkStatus } from "@/lib/api";
import { useSession } from "@/lib/session";
import { TECHNIQUES } from "@/lib/techniques";
import { artworkPath } from "@/lib/slug";
import { ImageEditor } from "@/components/panel/ImageEditor";
import { StatusBadge } from "@/components/StatusBadge";

const optionalNumber = z.preprocess((v) => (v === "" || v === null ? undefined : v), z.coerce.number().positive().optional());

const schema = z.object({
  title: z.string().trim().min(2, "Pon un título a la obra").max(200),
  technique: z.string().min(1),
  width: z.coerce.number().positive("Indica el ancho"),
  height: z.coerce.number().positive("Indica el alto"),
  year: z.coerce.number().int().min(1900, "Año no válido").max(2100, "Año no válido"),
  // Vacío = "Consultar precio"
  price: optionalNumber,
  description: z.string().max(4000, "Máximo 4000 caracteres").optional(),
  status: z.enum(["borrador", "publicado", "reservado", "vendido"]),
});
type FormIn = z.input<typeof schema>;
type FormOut = z.output<typeof schema>;

const STATUS_LABELS: Record<ArtworkStatus, string> = {
  borrador: "Borrador (solo tú la ves)",
  publicado: "Publicada",
  reservado: "Reservada",
  vendido: "Vendida",
};

const field = "w-full min-h-11 rounded-md border border-line bg-white px-3 text-base outline-none focus:border-gold md:text-sm";
const num = (s: string | null) => (s === null ? "" : String(Number(s)));

/** Edición de una obra ya creada: datos, estado y foto principal. */
export default function EditarObra() {
  const { id } = useParams<{ id: string }>();
  const { authFetch } = useSession();
  const [art, setArt] = useState<ArtworkDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoBusy, setPhotoBusy] = useState(false);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting, isDirty } } = useForm<FormIn, unknown, FormOut>({
    resolver: zodResolver(schema),
  });

  const fill = useCallback(
    (a: ArtworkDetail) => {
      setArt(a);
      reset({
        title: a.title, technique: a.technique, width: num(a.width_cm), height: num(a.height_cm), year: a.year,
        price: num(a.price), description: a.description ?? "", status: a.status,
      });
    },
    [reset],
  );

  useEffect(() => {
    authFetch<ArtworkDetail>(`/panel/artworks/${id}`).then(fill).catch(() => setLoadError("No se ha encontrado esta obra."));
  }, [authFetch, id, fill]);

  // Aviso del navegador si se sale con cambios sin guardar.
  useEffect(() => {
    if (!isDirty) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [isDirty]);

  async function save(d: FormOut) {
    setMsg(null);
    try {
      const updated = await authFetch<ArtworkDetail>(`/panel/artworks/${id}`, {
        method: "PATCH",
        json: {
          title: d.title, technique: d.technique, width_cm: d.width, height_cm: d.height, year: d.year,
          price: d.price ?? null, description: d.description?.trim() || null, status: d.status,
        },
      });
      fill(updated);
      setMsg({ ok: true, text: "Cambios guardados." });
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : "No se pudieron guardar los cambios." });
    }
  }

  /** Sube la foto nueva y después borra las anteriores: una obra publicada nunca se queda sin foto. */
  async function replacePhoto(blob: Blob) {
    if (!art) return;
    setPhotoBusy(true);
    setMsg(null);
    try {
      const fd = new FormData();
      fd.append("file", blob, "obra.webp");
      fd.append("alt_text", art.title);
      await authFetch(`/panel/artworks/${id}/images`, { method: "POST", body: fd });
      for (const im of art.images) await authFetch(`/panel/artworks/${id}/images/${im.id}`, { method: "DELETE" });
      const updated = await authFetch<ArtworkDetail>(`/panel/artworks/${id}`);
      setArt(updated);
      setPhotoFile(null);
      setMsg({ ok: true, text: "Foto actualizada." });
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : "No se pudo cambiar la foto." });
    } finally {
      setPhotoBusy(false);
    }
  }

  if (loadError)
    return (
      <div className="py-10 text-center">
        <p role="alert" className="text-sm text-red-700">{loadError}</p>
        <Link href="/panel/obras" className="mt-4 inline-block text-sm underline">Volver a Mis obras</Link>
      </div>
    );
  if (!art) return <p className="py-10 text-center text-sm text-muted">Cargando…</p>;

  if (photoFile)
    return (
      <>
        <h1 className="mb-4 font-serif text-3xl">Nueva foto de «{art.title}»</h1>
        {photoBusy ? (
          <p className="py-10 text-center text-sm text-muted">Subiendo la foto…</p>
        ) : (
          <ImageEditor file={photoFile} onBack={() => setPhotoFile(null)} onDone={(b) => void replacePhoto(b)} />
        )}
      </>
    );

  const main = art.images[0];
  const techniques = TECHNIQUES.includes(art.technique) ? TECHNIQUES : [art.technique, ...TECHNIQUES];

  return (
    <>
      <Link href="/panel/obras" className="inline-flex min-h-11 items-center gap-2 text-sm text-muted hover:text-foreground">
        <ArrowLeft size={16} aria-hidden /> Mis obras
      </Link>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <h1 className="font-serif text-3xl md:text-4xl">Editar obra</h1>
        <StatusBadge status={art.status} className="border border-line shadow-none" />
      </div>

      <form noValidate onSubmit={handleSubmit(save)} className="mt-6 grid gap-8 md:grid-cols-[280px_minmax(0,1fr)]">
        <div>
          <div className="flex aspect-square items-center justify-center bg-[#ece8e0] p-[10%]">
            {main ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={main.thumb_url} alt={art.title} className="max-h-full max-w-full shadow-md" />
            ) : (
              <span className="text-xs text-muted">Sin foto</span>
            )}
          </div>
          <label className="mt-3 flex min-h-11 cursor-pointer items-center justify-center gap-2 border border-line text-sm">
            <ImagePlus size={16} aria-hidden /> {main ? "Cambiar foto" : "Añadir foto"}
            <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(e) => e.target.files?.[0] && setPhotoFile(e.target.files[0])} />
          </label>
          {art.status !== "borrador" && (
            <Link href={artworkPath(art.id, art.title)} target="_blank" className="mt-2 flex min-h-11 items-center justify-center gap-2 text-sm underline">
              <ExternalLink size={14} aria-hidden /> Ver en la web
            </Link>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <label htmlFor="title" className="mb-1 block text-xs">Título</label>
            <input id="title" className={field} {...register("title")} />
            {errors.title && <p className="mt-1 text-xs text-red-700">{errors.title.message}</p>}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="technique" className="mb-1 block text-xs">Técnica</label>
              <select id="technique" className={field} {...register("technique")}>
                {techniques.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="status" className="mb-1 block text-xs">Estado</label>
              <select id="status" className={field} {...register("status")}>
                {(Object.keys(STATUS_LABELS) as ArtworkStatus[]).map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label htmlFor="width" className="mb-1 block text-xs">Ancho (cm)</label>
              <input id="width" inputMode="decimal" className={field} {...register("width")} />
            </div>
            <div>
              <label htmlFor="height" className="mb-1 block text-xs">Alto (cm)</label>
              <input id="height" inputMode="decimal" className={field} {...register("height")} />
            </div>
            <div>
              <label htmlFor="year" className="mb-1 block text-xs">Año</label>
              <input id="year" inputMode="numeric" className={field} {...register("year")} />
            </div>
          </div>
          {(errors.width || errors.height || errors.year) && <p className="text-xs text-red-700">Revisa las medidas y el año.</p>}
          <div>
            <label htmlFor="price" className="mb-1 block text-xs">Precio (€)</label>
            <input id="price" inputMode="decimal" placeholder="Vacío = «Consultar precio»" className={field} {...register("price")} />
            {errors.price && <p className="mt-1 text-xs text-red-700">Indica un precio válido o déjalo vacío.</p>}
          </div>
          <div>
            <label htmlFor="description" className="mb-1 block text-xs">Historia de la obra</label>
            <textarea id="description" rows={6} className={field.replace("min-h-11", "py-2")} {...register("description")} />
            {errors.description && <p className="mt-1 text-xs text-red-700">{errors.description.message}</p>}
          </div>

          {msg && <p role={msg.ok ? "status" : "alert"} className={`text-sm ${msg.ok ? "text-gold" : "text-red-700"}`}>{msg.text}</p>}

          <div className="sticky bottom-20 z-10 flex gap-3 bg-background py-3 md:static">
            <button
              type="button" disabled={!isDirty || isSubmitting} onClick={() => art && fill(art)}
              className="min-h-12 flex-1 border border-line text-sm disabled:opacity-50 md:flex-none md:px-6"
            >
              Descartar
            </button>
            <button type="submit" disabled={isSubmitting} className="min-h-12 flex-1 bg-foreground text-xs uppercase tracking-[0.18em] text-background disabled:opacity-60 md:flex-none md:px-8">
              {isSubmitting ? "Guardando…" : "Guardar cambios"}
            </button>
          </div>
        </div>
      </form>
    </>
  );
}
