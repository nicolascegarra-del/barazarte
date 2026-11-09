"use client";

import { useEffect, useState } from "react";

/**
 * Barra fija inferior en móvil con el precio y "Contactar": lleva al formulario y enfoca el primer campo.
 * Se oculta cuando el formulario ya está a la vista para no taparlo.
 */
export function ContactBar({ price, targetId }: { price: string; targetId: string }) {
  const [formVisible, setFormVisible] = useState(false);

  useEffect(() => {
    const el = document.getElementById(targetId);
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => setFormVisible(entry.isIntersecting), { threshold: 0.15 });
    io.observe(el);
    return () => io.disconnect();
  }, [targetId]);

  function go() {
    const el = document.getElementById(targetId);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
    setTimeout(() => el?.querySelector<HTMLInputElement>("input")?.focus({ preventScroll: true }), 450);
  }

  return (
    <div
      aria-hidden={formVisible}
      className={`fixed inset-x-0 bottom-0 z-20 border-t border-line bg-background/95 px-4 pb-[calc(env(safe-area-inset-bottom)+12px)] pt-3 backdrop-blur transition-transform duration-200 md:hidden ${formVisible ? "translate-y-full" : ""}`}
    >
      <div className="flex items-center justify-between gap-4">
        <p className="text-lg">{price}</p>
        <button type="button" tabIndex={formVisible ? -1 : 0} onClick={go} className="min-h-12 flex-1 bg-foreground px-5 text-xs uppercase tracking-[0.18em] text-background">
          Contactar
        </button>
      </div>
    </div>
  );
}
