import Link from "next/link";
import { Logo } from "./Logo";

const LEGAL = [
  { href: "/legal/aviso-legal", label: "Aviso legal" },
  { href: "/legal/privacidad", label: "Privacidad" },
  { href: "/legal/cookies", label: "Cookies" },
];

export function Footer() {
  return (
    <footer className="mt-16 border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-muted md:flex-row md:items-center md:justify-between md:px-8">
        <Logo className="text-2xl text-foreground" />
        <p>Obra original. Trato directo con cada artista.</p>
        <nav aria-label="Textos legales" className="flex flex-wrap gap-x-5">
          {LEGAL.map((l) => (
            <Link key={l.href} href={l.href} className="min-h-11 content-center hover:text-foreground">{l.label}</Link>
          ))}
        </nav>
        <p>© {new Date().getFullYear()} BarazArte</p>
      </div>
    </footer>
  );
}
