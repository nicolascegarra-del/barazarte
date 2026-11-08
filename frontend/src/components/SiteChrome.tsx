"use client";

import { usePathname } from "next/navigation";

// Rutas con cabecera propia (panel, admin y pantallas de cuenta): ahí no se muestra la cabecera/pie públicos.
const OWN_CHROME = ["/panel", "/admin", "/registro", "/verificar-email", "/recuperar", "/restablecer"];

export function SiteChrome({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return OWN_CHROME.some((p) => path.startsWith(p)) ? null : <>{children}</>;
}
