"use client";

import { usePathname } from "next/navigation";

/** Oculta la cabecera/pie públicos dentro del panel del artista, que tiene los suyos. */
export function SiteChrome({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return path.startsWith("/panel") ? null : <>{children}</>;
}
