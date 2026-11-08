"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { publicPost } from "@/lib/api";
import { authButton, authField } from "./AuthCard";

const schema = z
  .object({
    display_name: z.string().trim().min(2, "Escribe tu nombre artístico"),
    email: z.string().email("Email no válido"),
    password: z.string().min(10, "Mínimo 10 caracteres"),
    confirm: z.string(),
    accept_privacy: z.boolean().refine((v) => v, "Debes aceptar la política de privacidad"),
  })
  .refine((d) => d.password === d.confirm, { path: ["confirm"], message: "Las contraseñas no coinciden" });
type Data = z.infer<typeof schema>;

export function RegisterForm() {
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Data>({ resolver: zodResolver(schema) });

  async function onSubmit(d: Data) {
    setError(null);
    try {
      await publicPost("/auth/register", {
        email: d.email, display_name: d.display_name, password: d.password, accept_privacy: true,
      });
      setSentTo(d.email);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo crear la cuenta.");
    }
  }

  if (sentTo)
    return (
      <div role="status" className="space-y-3 text-sm">
        <p>Te hemos enviado un email a <strong>{sentTo}</strong>. Pulsa el enlace para activar tu cuenta.</p>
        <p className="text-muted">Si no lo ves, revisa la carpeta de spam. El enlace caduca en 48 horas.</p>
      </div>
    );

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <div>
        <label htmlFor="display_name" className="mb-1 block text-xs">Nombre artístico</label>
        <input id="display_name" autoComplete="name" className={authField} {...register("display_name")} />
        {errors.display_name && <p className="mt-1 text-xs text-red-700">{errors.display_name.message}</p>}
      </div>
      <div>
        <label htmlFor="email" className="mb-1 block text-xs">Email</label>
        <input id="email" type="email" autoComplete="email" className={authField} {...register("email")} />
        {errors.email && <p className="mt-1 text-xs text-red-700">{errors.email.message}</p>}
      </div>
      <div>
        <label htmlFor="password" className="mb-1 block text-xs">Contraseña</label>
        <input id="password" type="password" autoComplete="new-password" className={authField} {...register("password")} />
        {errors.password && <p className="mt-1 text-xs text-red-700">{errors.password.message}</p>}
      </div>
      <div>
        <label htmlFor="confirm" className="mb-1 block text-xs">Repite la contraseña</label>
        <input id="confirm" type="password" autoComplete="new-password" className={authField} {...register("confirm")} />
        {errors.confirm && <p className="mt-1 text-xs text-red-700">{errors.confirm.message}</p>}
      </div>
      <label className="flex min-h-11 items-start gap-3 text-xs text-muted">
        <input type="checkbox" className="mt-0.5 h-5 w-5 accent-[#8a6d2f]" {...register("accept_privacy")} />
        Acepto la política de privacidad y que mis datos se traten para gestionar mi cuenta.
      </label>
      {errors.accept_privacy && <p className="text-xs text-red-700">{errors.accept_privacy.message}</p>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button disabled={isSubmitting} className={authButton}>{isSubmitting ? "Creando cuenta…" : "Crear cuenta"}</button>
      <p className="text-center text-sm text-muted">¿Ya tienes cuenta? <Link href="/panel" className="underline">Entrar</Link></p>
    </form>
  );
}
