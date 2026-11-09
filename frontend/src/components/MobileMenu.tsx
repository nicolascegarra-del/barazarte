"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";

const LINKS = [
  { href: "/", label: "Inicio" },
  { href: "/obras", label: "Obras" },
  { href: "/panel", label: "Soy artista · Entrar" },
  { href: "/registro", label: "Exponer mis obras" },
];

/** Menú hamburguesa para móvil: panel a pantalla completa con enlaces grandes; se cierra al navegar o con Esc. */
export function MobileMenu() {
  const [open, setOpen] = useState(false);
  const path = usePathname();

  useEffect(() => setOpen(false), [path]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden"; // evita que la página se desplace por detrás
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <div className="md:hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="menu-movil"
        aria-label={open ? "Cerrar menú" : "Abrir menú"}
        className="-mr-2 flex h-11 w-11 items-center justify-center"
      >
        {open ? <X size={24} aria-hidden /> : <Menu size={24} aria-hidden />}
      </button>
      {open && (
        <nav id="menu-movil" aria-label="Menú" className="fixed inset-x-0 bottom-0 top-[65px] z-40 overflow-y-auto bg-background px-4 pb-10 pt-4">
          <ul className="divide-y divide-line border-y border-line">
            {LINKS.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  aria-current={path === l.href ? "page" : undefined}
                  className={`flex min-h-14 items-center font-serif text-2xl ${path === l.href ? "text-gold" : ""}`}
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
          <div className="mt-8 flex flex-wrap gap-x-5 text-sm text-muted">
            <Link href="/legal/aviso-legal" className="min-h-11 content-center">Aviso legal</Link>
            <Link href="/legal/privacidad" className="min-h-11 content-center">Privacidad</Link>
            <Link href="/legal/cookies" className="min-h-11 content-center">Cookies</Link>
          </div>
        </nav>
      )}
    </div>
  );
}
