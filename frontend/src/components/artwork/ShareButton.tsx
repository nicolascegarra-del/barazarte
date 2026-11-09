"use client";

import { useState } from "react";
import { Share2 } from "lucide-react";

/** Comparte la obra con el menú nativo del móvil (WhatsApp, Instagram…); en ordenador copia el enlace. */
export function ShareButton({ title, text }: { title: string; text: string }) {
  const [copied, setCopied] = useState(false);

  async function share() {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title, text, url });
      } catch {
        /* el usuario canceló */
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      window.prompt("Copia este enlace:", url);
    }
  }

  return (
    <button type="button" onClick={share} className="inline-flex min-h-11 items-center gap-2 border border-line px-4 text-sm hover:border-foreground">
      <Share2 size={16} aria-hidden />
      <span aria-live="polite">{copied ? "Enlace copiado" : "Compartir"}</span>
    </button>
  );
}
