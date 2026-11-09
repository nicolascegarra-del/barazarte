import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond, Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { SiteChrome } from "@/components/SiteChrome";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  variable: "--font-cormorant",
});
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

// URL pública de la web (para que las vistas previas al compartir lleven enlaces absolutos). Se lee en ejecución.
const SITE_URL = process.env.SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "BarazArte · Galería de arte online",
  description: "Obras originales de artistas contemporáneos. Contacta directamente con el artista.",
  openGraph: {
    type: "website",
    siteName: "BarazArte",
    locale: "es_ES",
    title: "BarazArte · Galería de arte online",
    description: "Obras originales de artistas contemporáneos. Contacta directamente con el artista.",
    images: [{ url: "/icons/icon-512.png", width: 512, height: 512, alt: "BarazArte" }],
  },
  twitter: { card: "summary" },
  // Al añadir la web a la pantalla de inicio se comporta como app (necesario para avisos en iPhone).
  appleWebApp: { capable: true, title: "BarazArte", statusBarStyle: "default" },
  icons: { icon: "/icons/icon-192.png", apple: "/icons/apple-touch-icon.png" },
};

export const viewport: Viewport = { themeColor: "#faf8f4" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${cormorant.variable} ${inter.variable}`}>
      <body className="min-h-screen flex flex-col antialiased">
        <SiteChrome><Header /></SiteChrome>
        <main className="flex-1">{children}</main>
        <SiteChrome><Footer /></SiteChrome>
      </body>
    </html>
  );
}
