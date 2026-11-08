import Link from "next/link";
import { type ArtworkListItem, type Page, publicGet } from "@/lib/api";
import { ArtworkGrid } from "@/components/ArtworkGrid";

export const dynamic = "force-dynamic";

export default async function Home() {
  const data = await publicGet<Page<ArtworkListItem>>("/artworks?page_size=6");
  return (
    <>
      <section className="mx-auto grid max-w-6xl gap-6 px-4 pb-4 pt-12 md:grid-cols-2 md:items-end md:px-8 md:pt-16">
        <h1 className="font-serif text-4xl font-medium leading-[1.05] md:text-6xl">
          Pintura contemporánea, obra original
        </h1>
        <div>
          <p className="text-sm leading-7 text-muted">
            Cada pieza es única y está firmada por su autor. Descubre la colección y contacta directamente con el
            artista para hacerla tuya.
          </p>
          <Link
            href="/obras"
            className="mt-5 inline-flex min-h-11 items-center border border-foreground px-6 text-xs uppercase tracking-[0.18em] hover:bg-foreground hover:text-background"
          >
            Ver todas las obras
          </Link>
        </div>
      </section>
      <section aria-label="Obras destacadas" className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <ArtworkGrid data={data} />
      </section>
    </>
  );
}
