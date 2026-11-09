import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/seo";

/** Qué pueden rastrear los buscadores: todo lo público; nunca el panel, la administración ni las cuentas. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/panel", "/admin", "/verificar-email", "/recuperar", "/restablecer"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
