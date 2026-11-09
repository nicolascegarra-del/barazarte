import Link from "next/link";
import { Logo } from "./Logo";
import { MobileMenu } from "./MobileMenu";

const links = [
  { href: "/obras", label: "Obras" },
  { href: "/panel", label: "Soy artista" },
];

export function Header() {
  return (
    // Fija arriba: en móvil el menú está siempre a mano sin volver al principio de la página.
    // Sin backdrop-blur: crearía un bloque contenedor y el menú (position: fixed) quedaría atrapado en la cabecera.
    <header className="sticky top-0 z-30 h-[65px] border-b border-line bg-background">
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between gap-3 px-4 md:px-8">
        <Logo />
        <nav aria-label="Principal" className="hidden gap-8 text-[11px] uppercase tracking-[0.2em] md:flex">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="py-3 hover:text-gold">
              {l.label}
            </Link>
          ))}
        </nav>
        <MobileMenu />
      </div>
    </header>
  );
}
