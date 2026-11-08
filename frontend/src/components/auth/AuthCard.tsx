import { Logo } from "@/components/Logo";

export const authField =
  "w-full min-h-12 rounded-md border border-line bg-white px-3 text-base outline-none focus:border-gold";
export const authButton =
  "min-h-12 w-full bg-foreground text-xs uppercase tracking-[0.18em] text-background hover:bg-gold disabled:opacity-60";

/** Marco común de las pantallas de cuenta (registro, verificar email, recuperar clave). */
export function AuthCard({ title, intro, children }: { title: string; intro?: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto min-h-screen max-w-sm px-4 py-8">
      <Logo className="text-2xl" />
      <h1 className="mt-10 font-serif text-3xl">{title}</h1>
      {intro && <p className="mt-2 text-sm text-muted">{intro}</p>}
      <div className="mt-6">{children}</div>
    </div>
  );
}
