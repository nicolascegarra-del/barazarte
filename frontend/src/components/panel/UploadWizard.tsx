"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Camera, ImagePlus, Check, Sun, Frame, Maximize } from "lucide-react";
import { useSession } from "@/lib/session";
import { ImageEditor } from "./ImageEditor";

const schema = z.object({
  title: z.string().min(2, "Pon un título a la obra"),
  technique: z.string().min(1),
  width: z.coerce.number().positive("Indica el ancho"),
  height: z.coerce.number().positive("Indica el alto"),
  year: z.coerce.number().int().min(1900).max(2100),
  price: z.coerce.number().positive("Indica el precio"),
  story: z.string().optional(),
});
type FormIn = z.input<typeof schema>;
type FormOut = z.output<typeof schema>;

const TECHNIQUES = ["Óleo sobre lienzo", "Acrílico sobre lienzo", "Acuarela", "Técnica mixta", "Dibujo", "Otra"];
const field = "w-full min-h-11 rounded-md border border-line bg-white px-3 text-base outline-none focus:border-gold md:text-sm";
const steps = ["Foto", "Ajustes", "Datos"];

/**
 * Asistente de subida en 3 pasos pensado primero para móvil:
 * 1) hacer foto o elegir de la galería, 2) ajustar la imagen, 3) rellenar datos y publicar.
 */
export function UploadWizard() {
  const [step, setStep] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [published, setPublished] = useState<"publicado" | "borrador" | null>(null);
  const { authFetch, artist, reloadMe } = useSession();
  const [blob, setBlob] = useState<Blob | null>(null);
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [imageUploaded, setImageUploaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Solo se bloquea antes de crear la obra; si ya se creó en este asistente, se deja terminar.
  const limitReached =
    !!artist && artist.max_artworks !== null && artist.artworks_count >= artist.max_artworks && createdId === null && !published;
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormIn, unknown, FormOut>({
    resolver: zodResolver(schema),
    defaultValues: { technique: TECHNIQUES[0], year: new Date().getFullYear() },
  });

  function pick(f: File | undefined) {
    if (!f) return;
    setFile(f);
    setStep(1);
  }

  /**
   * Crea la obra como borrador, sube la foto y, si se publica, cambia el estado.
   * Se guarda el id creado para que un reintento tras un fallo no duplique la obra.
   */
  async function save(status: "publicado" | "borrador", data: FormOut) {
    if (!blob) return;
    setError(null);
    try {
      let id = createdId;
      if (id === null) {
        const art = await authFetch<{ id: number }>("/panel/artworks", {
          method: "POST",
          json: {
            title: data.title, technique: data.technique, width_cm: data.width, height_cm: data.height,
            year: data.year, price: data.price, description: data.story || null, status: "borrador",
          },
        });
        id = art.id;
        setCreatedId(id);
      }
      if (!imageUploaded) {
        const fd = new FormData();
        fd.append("file", blob, "obra.webp");
        fd.append("alt_text", data.title);
        await authFetch(`/panel/artworks/${id}/images`, { method: "POST", body: fd });
        setImageUploaded(true);
      }
      if (status === "publicado") await authFetch(`/panel/artworks/${id}`, { method: "PATCH", json: { status } });
      setPublished(status);
      void reloadMe(); // actualiza el contador "X de Y obras"
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo guardar la obra. Inténtalo de nuevo.");
    }
  }

  if (limitReached)
    return (
      <div role="status" className="mx-auto max-w-md py-10 text-center">
        <h1 className="font-serif text-3xl">Has llegado al límite de obras</h1>
        <p className="mt-2 text-sm text-muted">
          Tu cuenta permite {artist?.max_artworks} obras y ya las has usado. Puedes borrar una que ya no necesites desde Mis obras
          o escribirnos para ampliar tu límite.
        </p>
        <Link href="/panel/obras" className="mt-6 inline-flex min-h-12 items-center bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background">Ir a Mis obras</Link>
      </div>
    );

  if (published)
    return (
      <div className="mx-auto max-w-md py-10 text-center">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-foreground text-background"><Check aria-hidden /></span>
        <h1 className="mt-5 font-serif text-3xl">{published === "publicado" ? "Obra publicada" : "Borrador guardado"}</h1>
        <p className="mt-2 text-sm text-muted">
          {published === "publicado" ? "Ya la puede ver cualquier visitante de BarazArte." : "Puedes terminarla cuando quieras desde Mis obras."}
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <button onClick={() => { setPublished(null); setFile(null); setPreview(null); setBlob(null); setCreatedId(null); setImageUploaded(false); setStep(0); }} className="min-h-12 bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background">Subir otra obra</button>
          <Link href="/panel" className="inline-flex min-h-12 items-center justify-center border border-line px-6 text-sm">Volver al resumen</Link>
        </div>
      </div>
    );

  return (
    <div>
      <ol className="mb-6 flex items-center gap-2 text-xs" aria-label="Progreso">
        {steps.map((s, i) => (
          <li key={s} aria-current={i === step ? "step" : undefined} className={`flex flex-1 items-center gap-2 border-t-2 pt-2 ${i <= step ? "border-gold text-foreground" : "border-line text-muted"}`}>
            {i + 1}. {s}
          </li>
        ))}
      </ol>

      {step === 0 && (
        <div className="mx-auto max-w-lg">
          <h1 className="font-serif text-3xl md:text-4xl">Sube tu obra</h1>
          <p className="mt-2 text-sm text-muted">Haz una foto del cuadro o elige una que ya tengas.</p>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {/* capture="environment" abre directamente la cámara trasera en móvil */}
            <label className="flex min-h-28 cursor-pointer flex-col items-center justify-center gap-2 bg-foreground p-4 text-background">
              <Camera aria-hidden /> <span className="text-sm">Hacer foto</span>
              <input type="file" accept="image/*" capture="environment" className="sr-only" onChange={(e) => pick(e.target.files?.[0])} />
            </label>
            <label className="flex min-h-28 cursor-pointer flex-col items-center justify-center gap-2 border border-foreground p-4">
              <ImagePlus aria-hidden /> <span className="text-sm">Elegir de la galería</span>
              <input type="file" accept="image/jpeg,image/png,image/webp,image/heic" className="sr-only" onChange={(e) => pick(e.target.files?.[0])} />
            </label>
          </div>
          <p className="mt-3 hidden text-center text-xs text-muted md:block">O arrastra el archivo aquí desde tu ordenador</p>

          <ul className="mt-8 space-y-3 text-sm text-muted">
            <li className="flex gap-3"><Sun size={18} className="shrink-0 text-gold" aria-hidden /> Luz natural, sin flash ni reflejos.</li>
            <li className="flex gap-3"><Frame size={18} className="shrink-0 text-gold" aria-hidden /> De frente, con el cuadro recto y entero.</li>
            <li className="flex gap-3"><Maximize size={18} className="shrink-0 text-gold" aria-hidden /> Después podrás recortar, enderezar y ajustar el color.</li>
          </ul>
        </div>
      )}

      {step === 1 && file && (
        <ImageEditor
          file={file}
          onBack={() => setStep(0)}
          onDone={(b, url) => { setBlob(b); setPreview(url); setImageUploaded(false); setStep(2); }}
        />
      )}

      {step === 2 && (
        <form noValidate className="grid gap-8 md:grid-cols-[280px_minmax(0,1fr)]" onSubmit={handleSubmit((d) => save("publicado", d))}>
          <div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            {preview && <img src={preview} alt="Foto de la obra ya ajustada" className="mx-auto max-h-72 w-auto shadow-md md:max-h-none md:w-full" />}
            <button type="button" onClick={() => setStep(1)} className="mt-3 w-full min-h-11 text-sm underline">Volver a ajustar la foto</button>
          </div>
          <div className="space-y-4">
            <div>
              <label htmlFor="title" className="mb-1 block text-xs">Título</label>
              <input id="title" className={field} {...register("title")} />
              {errors.title && <p className="mt-1 text-xs text-red-700">{errors.title.message}</p>}
            </div>
            <div>
              <label htmlFor="technique" className="mb-1 block text-xs">Técnica</label>
              <select id="technique" className={field} {...register("technique")}>
                {TECHNIQUES.map((t) => <option key={t}>{t}</option>)}
              </select>
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
            {(errors.width || errors.height) && <p className="text-xs text-red-700">Indica las medidas de la obra.</p>}
            <div>
              <label htmlFor="price" className="mb-1 block text-xs">Precio (€)</label>
              <input id="price" inputMode="decimal" className={field} {...register("price")} />
              {errors.price && <p className="mt-1 text-xs text-red-700">{errors.price.message}</p>}
            </div>
            <div>
              <label htmlFor="story" className="mb-1 block text-xs">Historia de la obra (opcional)</label>
              <textarea id="story" rows={4} className={field.replace("min-h-11", "py-2")} {...register("story")} />
            </div>
            {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
            <div className="sticky bottom-20 z-10 flex gap-3 bg-background py-3 md:static">
              <button type="button" onClick={handleSubmit((d) => save("borrador", d))} className="min-h-12 flex-1 border border-line text-sm md:flex-none md:px-6">Guardar borrador</button>
              <button type="submit" disabled={isSubmitting} className="min-h-12 flex-1 bg-foreground text-xs uppercase tracking-[0.18em] text-background md:flex-none md:px-8">Publicar</button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
