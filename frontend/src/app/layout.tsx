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

export const metadata: Metadata = {
  title: "BarazArte · Galería de arte online",
  description: "Obras originales de artistas contemporáneos. Contacta directamente con el artista.",
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
