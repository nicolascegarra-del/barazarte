"use client";

import { useEffect } from "react";
import { API_URL } from "@/lib/api";

/**
 * Cuenta una visita de forma anónima: sin cookies, sin IDs de usuario ni datos personales.
 * `keepalive` permite que la petición termine aunque el usuario cambie de página.
 */
export function VisitTracker({ artworkId }: { artworkId?: number }) {
  useEffect(() => {
    fetch(`${API_URL}/track`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ artwork_id: artworkId ?? null }),
      keepalive: true,
      credentials: "omit",
    }).catch(() => undefined); // las estadísticas nunca deben romper la página
  }, [artworkId]);
  return null;
}
