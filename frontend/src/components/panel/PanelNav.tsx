"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Image as ImageIcon, LayoutDashboard, Mail, MailCheck, Plus, Shield, Users } from "lucide-react";
import { useSession } from "@/lib/session";
import { useUnread } from "@/lib/unread";

const CONSULTAS = "/panel/consultas";

/** Contador rojo de consultas sin leer (oculto si es 0; "99+" a partir de 100). */
function Counter({ n, className = "" }: { n: number; className?: string }) {
  if (n <= 0) return null;
  return (
    <span aria-hidden className={`inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-[#b3261e] px-1 text-[10px] font-semibold leading-none text-white ${className}`}>
      {n > 99 ? "99+" : n}
    </span>
  );
}

type Item = { href: string; label: string; icon: typeof Home };

const artistItems: Item[] = [
  { href: "/panel", label: "Resumen", icon: Home },
  { href: "/panel/obras", label: "Mis obras", icon: ImageIcon },
  { href: "/panel/consultas", label: "Consultas", icon: Mail },
];
const adminItems: Item[] = [
  { href: "/admin", label: "Resumen", icon: LayoutDashboard },
  { href: "/admin/artistas", label: "Artistas", icon: Users },
  { href: "/admin/correo", label: "Correo", icon: MailCheck },
];

/**
 * Navegación del panel. Móvil: barra inferior (alcance con el pulgar) con "+" central para subir obra.
 * Escritorio: enlaces arriba. Dentro de /admin se muestran las secciones de administración
 * y un acceso de vuelta a "Mi panel"; los administradores ven el acceso a /admin desde su panel.
 */
export function PanelNav() {
  const path = usePathname();
  const { artist } = useSession();
  const { count: unread } = useUnread();
  const inAdmin = path.startsWith("/admin");
  const items = inAdmin ? adminItems : artistItems;
  const exact = inAdmin ? "/admin" : "/panel";
  const active = (href: string) => (href === exact ? path === href : path.startsWith(href));
  const cls = (on: boolean) => (on ? "text-gold" : "text-muted");

  // Enlace de cambio de zona: solo para administradores.
  const switchTo: Item | null = artist?.is_admin
    ? inAdmin
      ? { href: "/panel", label: "Mi panel", icon: ImageIcon }
      : { href: "/admin", label: "Admin", icon: Shield }
    : null;

  return (
    <>
      <nav aria-label={inAdmin ? "Administración" : "Panel"} className="hidden items-center gap-6 md:flex">
        {items.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            aria-current={active(href) ? "page" : undefined}
            aria-label={href === CONSULTAS && unread > 0 ? `${label}, ${unread} sin leer` : undefined}
            className={`inline-flex items-center gap-1.5 py-2 text-sm ${active(href) ? "border-b border-gold text-foreground" : "text-muted hover:text-foreground"}`}
          >
            {label}
            {href === CONSULTAS && <Counter n={unread} />}
          </Link>
        ))}
        {switchTo && <Link href={switchTo.href} className="py-2 text-sm text-gold hover:underline">{switchTo.label}</Link>}
        {!inAdmin && (
          <Link
            href="/panel/subir"
            className="inline-flex min-h-10 items-center gap-2 bg-foreground px-4 text-xs uppercase tracking-[0.15em] text-background hover:bg-gold"
          >
            <Plus size={16} aria-hidden /> Subir obra
          </Link>
        )}
      </nav>

      <nav
        aria-label={inAdmin ? "Administración" : "Panel"}
        className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-4 items-end border-t border-line bg-background pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {inAdmin ? (
          <>
            {items.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} aria-current={active(href) ? "page" : undefined} className={`flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] ${cls(active(href))}`}>
                <Icon size={20} aria-hidden /> {label}
              </Link>
            ))}
            {switchTo && (
              <Link href={switchTo.href} className="flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] text-muted">
                <switchTo.icon size={20} aria-hidden /> {switchTo.label}
              </Link>
            )}
          </>
        ) : (
          <>
            {items.slice(0, 2).map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} aria-current={active(href) ? "page" : undefined} className={`flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] ${cls(active(href))}`}>
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
            <Link
              href={items[2].href}
              aria-current={active(items[2].href) ? "page" : undefined}
              aria-label={unread > 0 ? `${items[2].label}, ${unread} sin leer` : undefined}
              className={`flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] ${cls(active(items[2].href))}`}
            >
              <span className="relative">
                <Mail size={20} aria-hidden />
                <Counter n={unread} className="absolute -right-3 -top-2" />
              </span>
              {items[2].label}
            </Link>
            {switchTo && (
              <Link href={switchTo.href} className="absolute -top-9 right-3 inline-flex min-h-9 items-center gap-1 rounded-full border border-line bg-background px-3 text-[11px] text-gold">
                <Shield size={14} aria-hidden /> {switchTo.label}
              </Link>
            )}
          </>
        )}
      </nav>
    </>
  );
}
