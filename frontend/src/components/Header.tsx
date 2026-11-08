import Link from "next/link";
import { Logo } from "./Logo";

const links = [
  { href: "/obras", label: "Obras" },
  { href: "/panel", label: "Soy artista" },
];

export function Header() {
  return (
    <header className="border-b border-line">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4 md:px-8">
        <Logo />
        <nav aria-label="Principal" className="flex gap-5 text-[11px] uppercase tracking-[0.2em] md:gap-8">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="py-3 hover:text-gold">
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
