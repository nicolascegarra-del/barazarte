"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { API_URL, parseResponse } from "@/lib/api";

const schema = z.object({
  name: z.string().min(2, "Escribe tu nombre"),
  email: z.string().email("Email no válido"),
  phone: z.string().regex(/^[0-9+()\-\s.]*$/, "Solo números y + ( ) -").max(30).optional(),
  message: z.string().min(10, "Cuéntale al artista qué te interesa (mínimo 10 caracteres)").max(2000),
  accept_privacy: z.boolean().refine((v) => v, "Debes aceptar la política de privacidad"),
  website: z.string().max(0).optional(), // honeypot anti-spam: debe quedar vacío
});
type FormData = z.infer<typeof schema>;

const input = "w-full rounded-md border border-line bg-white px-3 py-2.5 text-base outline-none focus:border-gold md:text-sm";

/** Formulario "Contactar con el artista": envía la consulta a la API, que avisa por email al artista. */
export function ContactForm({ artworkId, title }: { artworkId: number; title: string }) {
  const [state, setState] = useState<"idle" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormData) {
    setError(null);
    try {
      const res = await fetch(`${API_URL}/artworks/${artworkId}/inquiries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...data, website: data.website ?? "" }),
      });
      await parseResponse(res);
      setState("sent");
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo enviar. Inténtalo de nuevo.");
    }
  }

  if (state === "sent")
    return (
      <p role="status" className="rounded-lg border border-line bg-white p-5 text-sm">
        Mensaje enviado. El artista recibirá tus datos por email y se pondrá en contacto contigo.
      </p>
    );

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-3">
      <p className="text-sm text-muted">
        ¿Te interesa «{title}»? Escribe al artista y acordad el siguiente paso directamente.
      </p>
      <div>
        <label htmlFor="name" className="mb-1 block text-xs">Nombre</label>
        <input id="name" className={input} autoComplete="name" {...register("name")} />
        {errors.name && <p className="mt-1 text-xs text-red-700">{errors.name.message}</p>}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="email" className="mb-1 block text-xs">Email</label>
          <input id="email" type="email" className={input} autoComplete="email" {...register("email")} />
          {errors.email && <p className="mt-1 text-xs text-red-700">{errors.email.message}</p>}
        </div>
        <div>
          <label htmlFor="phone" className="mb-1 block text-xs">Teléfono (opcional)</label>
          <input id="phone" type="tel" className={input} autoComplete="tel" {...register("phone")} />
          {errors.phone && <p className="mt-1 text-xs text-red-700">{errors.phone.message}</p>}
        </div>
      </div>
      <div>
        <label htmlFor="message" className="mb-1 block text-xs">Mensaje</label>
        <textarea id="message" rows={4} className={input} {...register("message")} />
        {errors.message && <p className="mt-1 text-xs text-red-700">{errors.message.message}</p>}
      </div>
      <label className="flex min-h-11 items-start gap-3 text-xs text-muted">
        <input type="checkbox" className="mt-0.5 h-5 w-5 accent-[#8a6d2f]" {...register("accept_privacy")} />
        Acepto que mis datos se envíen al artista para que pueda contactarme.
      </label>
      {errors.accept_privacy && <p className="text-xs text-red-700">{errors.accept_privacy.message}</p>}
      <input tabIndex={-1} autoComplete="off" aria-hidden="true" className="hidden" {...register("website")} />
      {error && <p role="alert" className="text-xs text-red-700">{error}</p>}
      <button
        type="submit"
        disabled={isSubmitting}
        className="min-h-11 w-full bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background hover:bg-gold disabled:opacity-60 sm:w-auto"
      >
        {isSubmitting ? "Enviando…" : "Contactar con el artista"}
      </button>
    </form>
  );
}
