import type { MetadataRoute } from "next";

/** Manifest de la app instalable (necesario para notificaciones en iPhone y para el número en el icono). */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "BarazArte",
    short_name: "BarazArte",
    description: "Galería de arte online. Panel para artistas.",
    start_url: "/panel",
    scope: "/",
    display: "standalone",
    background_color: "#faf8f4",
    theme_color: "#1c1c1c",
    lang: "es",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
