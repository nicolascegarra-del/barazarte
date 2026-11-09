import Link from "next/link";

/** Datos del titular pendientes: se muestran resaltados para que no pasen desapercibidos antes de publicar. */
export function Fill({ children }: { children: React.ReactNode }) {
  return <mark className="rounded bg-[#fdecc8] px-1 text-foreground">[COMPLETAR: {children}]</mark>;
}

const LINKS = [
  { href: "/legal/aviso-legal", label: "Aviso legal" },
  { href: "/legal/privacidad", label: "Privacidad" },
  { href: "/legal/cookies", label: "Cookies" },
];

/** Tabla con desplazamiento horizontal propio: en móvil no ensancha la página. */
export function LegalTable({ children }: { children: React.ReactNode }) {
  return (
    <div className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
      <table className="min-w-[560px]">{children}</table>
    </div>
  );
}

/** Plantilla común de las páginas legales: título, fecha de actualización y navegación entre ellas. */
export function LegalPage({ title, updated, current, children }: { title: string; updated: string; current: string; children: React.ReactNode }) {
  return (
    <article className="mx-auto max-w-3xl px-4 py-12 md:px-8">
      <nav aria-label="Textos legales" className="mb-8 flex flex-wrap gap-x-5 gap-y-2 text-xs uppercase tracking-[0.15em]">
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href} aria-current={l.href === current ? "page" : undefined} className={`min-h-11 content-center ${l.href === current ? "text-gold" : "text-muted hover:text-foreground"}`}>
            {l.label}
          </Link>
        ))}
      </nav>
      <h1 className="font-serif text-4xl font-medium md:text-5xl">{title}</h1>
      <p className="mt-2 text-xs text-muted">Última actualización: {updated}</p>
      <div className="legal mt-8 space-y-6 text-sm leading-7 [&_h2]:mt-10 [&_h2]:font-serif [&_h2]:text-2xl [&_h2]:font-medium [&_li]:ml-5 [&_li]:list-disc [&_table]:w-full [&_td]:border-t [&_td]:border-line [&_td]:py-2 [&_td]:pr-3 [&_td]:align-top [&_th]:pb-2 [&_th]:pr-3 [&_th]:text-left [&_th]:text-xs [&_th]:uppercase [&_th]:tracking-wider [&_th]:text-muted">
        {children}
      </div>
    </article>
  );
}
