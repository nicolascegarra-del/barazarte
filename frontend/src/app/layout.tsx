import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond, Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { SiteChrome } from "@/components/SiteChrome";
import { SITE_DESCRIPTION, SITE_NAME, SITE_URL } from "@/lib/seo";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  variable: "--font-cormorant",
});
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

const TITLE = "BarazArte · Galería de arte online y cuadros originales";

export const metadata: Metadata = {
  // SITE_URL llega en el build y en ejecución: enlaces absolutos correctos también en páginas estáticas.
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  // Sin canónica ni og:url aquí: se heredarían en todas las páginas. Cada página declara la suya.
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    locale: "es_ES",
    title: TITLE,
    description: SITE_DESCRIPTION,
    images: [{ url: "/icons/icon-512.png", width: 512, height: 512, alt: SITE_NAME }],
  },
  twitter: { card: "summary" },
  // Verificación de Google Search Console por etiqueta (opcional; alternativa al registro DNS).
  verification: process.env.GOOGLE_SITE_VERIFICATION ? { google: process.env.GOOGLE_SITE_VERIFICATION } : undefined,
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
