import { Logo } from "./Logo";

export function Footer() {
  return (
    <footer className="mt-16 border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-muted md:flex-row md:items-center md:justify-between md:px-8">
        <Logo className="text-2xl text-foreground" />
        <p>Obra original. Trato directo con cada artista.</p>
        <p>© {new Date().getFullYear()} BarazArte</p>
      </div>
    </footer>
  );
}
