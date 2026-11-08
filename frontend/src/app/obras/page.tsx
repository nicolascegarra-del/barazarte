import { type ArtworkListItem, type Page, publicGet } from "@/lib/api";
import { ArtworkGrid } from "@/components/ArtworkGrid";

export const metadata = { title: "Obras · BarazArte" };
export const dynamic = "force-dynamic";

export default async function Obras() {
  const data = await publicGet<Page<ArtworkListItem>>("/artworks?page_size=50");
  return (
    <section className="mx-auto max-w-6xl px-4 py-12 md:px-8">
      <h1 className="font-serif text-4xl font-medium md:text-5xl">Obras</h1>
      {data && <p className="mt-2 text-sm text-muted">{data.total} piezas.</p>}
      <div className="mt-10">
        <ArtworkGrid data={data} />
      </div>
    </section>
  );
}
