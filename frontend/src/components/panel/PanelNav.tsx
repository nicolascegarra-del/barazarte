"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Image as ImageIcon, Mail, Plus } from "lucide-react";

const items = [
  { href: "/panel", label: "Resumen", icon: Home },
  { href: "/panel/obras", label: "Mis obras", icon: ImageIcon },
  { href: "/panel/consultas", label: "Consultas", icon: Mail },
];

/**
 * Navegación del panel: barra inferior con botón "+" central en móvil (alcance con el pulgar)
 * y barra superior de enlaces en escritorio.
 */
export function PanelNav() {
  const path = usePathname();
  const active = (href: string) => (href === "/panel" ? path === href : path.startsWith(href));

  return (
    <>
      <nav aria-label="Panel" className="hidden items-center gap-6 md:flex">
        {items.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            aria-current={active(href) ? "page" : undefined}
            className={`py-2 text-sm ${active(href) ? "border-b border-gold text-foreground" : "text-muted hover:text-foreground"}`}
          >
            {label}
          </Link>
        ))}
        <Link
          href="/panel/subir"
          className="inline-flex min-h-10 items-center gap-2 bg-foreground px-4 text-xs uppercase tracking-[0.15em] text-background hover:bg-gold"
        >
          <Plus size={16} aria-hidden /> Subir obra
        </Link>
      </nav>

      <nav
        aria-label="Panel"
        className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-4 items-end border-t border-line bg-background pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {items.slice(0, 2).map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={active(href) ? "page" : undefined}
            className={`flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] ${active(href) ? "text-gold" : "text-muted"}`}
          >
            <Icon size={20} aria-hidden /> {label}
          </Link>
        ))}
        <Link
          href="/panel/subir"
          aria-label="Subir obra"
          className="-mt-5 flex h-14 w-14 items-center justify-center justify-self-center rounded-full bg-foreground text-background shadow-md"
        >
          <Plus size={26} aria-hidden />
        </Link>
        {items.slice(2).map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={active(href) ? "page" : undefined}
            className={`flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] ${active(href) ? "text-gold" : "text-muted"}`}
          >
            <Icon size={20} aria-hidden /> {label}
          </Link>
        ))}
      </nav>
    </>
  );
}
