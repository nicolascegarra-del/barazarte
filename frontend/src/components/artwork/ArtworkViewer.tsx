"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, X, ZoomIn } from "lucide-react";

interface Props {
  src: string;
  alt: string;
  width: number;
  height: number;
  badge?: React.ReactNode;
  prev: { id: number; title: string } | null;
  next: { id: number; title: string } | null;
}

const MAX_ZOOM = 5;

/** Foto a pantalla completa con zoom de dos dedos, doble toque para ampliar y arrastre para moverse. */
function Fullscreen({ src, alt, onClose }: { src: string; alt: string; onClose: () => void }) {
  const [t, setT] = useState({ s: 1, x: 0, y: 0 });
  const pointers = useRef(new Map<number, { x: number; y: number }>());
  const pinch = useRef<{ dist: number; s: number } | null>(null);
  const lastTap = useRef(0);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const dist = () => {
    const [a, b] = [...pointers.current.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  };

  function onDown(e: React.PointerEvent) {
    e.currentTarget.setPointerCapture(e.pointerId);
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.current.size === 2) pinch.current = { dist: dist(), s: t.s };
    if (pointers.current.size === 1) {
      const now = Date.now();
      if (now - lastTap.current < 300) setT((p) => (p.s > 1 ? { s: 1, x: 0, y: 0 } : { s: 2.5, x: 0, y: 0 }));
      lastTap.current = now;
    }
  }

  function onMove(e: React.PointerEvent) {
    const prev = pointers.current.get(e.pointerId);
    if (!prev) return;
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.current.size === 2 && pinch.current) {
      const s = Math.min(MAX_ZOOM, Math.max(1, (pinch.current.s * dist()) / pinch.current.dist));
      setT((p) => ({ ...p, s }));
    } else if (pointers.current.size === 1 && t.s > 1) {
      setT((p) => ({ ...p, x: p.x + e.clientX - prev.x, y: p.y + e.clientY - prev.y }));
    }
  }

  function onUp(e: React.PointerEvent) {
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) pinch.current = null;
    if (t.s <= 1) setT({ s: 1, x: 0, y: 0 });
  }

  return (
    <div role="dialog" aria-modal="true" aria-label={`${alt} a pantalla completa`} className="fixed inset-0 z-50 bg-[#111]">
      <div
        className="flex h-full w-full touch-none select-none items-center justify-center overflow-hidden"
        onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={onUp}
        onWheel={(e) => setT((p) => { const s = Math.min(MAX_ZOOM, Math.max(1, p.s * (e.deltaY < 0 ? 1.15 : 0.87))); return s <= 1 ? { s: 1, x: 0, y: 0 } : { ...p, s }; })}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src} alt={alt} draggable={false}
          style={{ transform: `translate(${t.x}px, ${t.y}px) scale(${t.s})` }}
          className="max-h-full max-w-full object-contain transition-transform duration-75"
        />
      </div>
      <button type="button" onClick={onClose} aria-label="Cerrar" className="absolute right-3 top-3 flex h-12 w-12 items-center justify-center rounded-full bg-white/15 text-white">
        <X size={24} aria-hidden />
      </button>
      <p className="pointer-events-none absolute inset-x-0 bottom-4 text-center text-xs text-white/70">
        Pellizca o toca dos veces para ampliar
      </p>
    </div>
  );
}

/**
 * Foto principal de la obra en su pared. Tocar abre la vista a pantalla completa;
 * deslizar a izquierda o derecha lleva a la obra siguiente o anterior.
 */
export function ArtworkViewer({ src, alt, width, height, badge, prev, next }: Props) {
  const router = useRouter();
  const [full, setFull] = useState(false);
  const start = useRef<{ x: number; y: number } | null>(null);
  const close = useCallback(() => setFull(false), []);

  function onTouchStart(e: React.TouchEvent) {
    start.current = e.touches.length === 1 ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : null;
  }
  function onTouchEnd(e: React.TouchEvent) {
    if (!start.current) return;
    const dx = e.changedTouches[0].clientX - start.current.x;
    const dy = e.changedTouches[0].clientY - start.current.y;
    start.current = null;
    // Solo gestos claramente horizontales, para no interferir con el desplazamiento vertical de la página.
    if (Math.abs(dx) < 60 || Math.abs(dy) > Math.abs(dx) * 0.6) return;
    const target = dx < 0 ? next : prev;
    if (target) router.push(`/obras/${target.id}`);
  }

  return (
    <div>
      <div className="relative bg-[#ece8e0]" onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
        <button type="button" onClick={() => setFull(true)} aria-label="Ver la obra a pantalla completa" className="group flex w-full items-center justify-center p-[8%]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={src} alt={alt} width={width} height={height} className="h-auto max-h-[70vh] w-auto max-w-full shadow-[0_10px_28px_rgba(0,0,0,.25)]" />
          <span className="absolute bottom-3 right-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-foreground shadow-sm" aria-hidden>
            <ZoomIn size={18} />
          </span>
        </button>
        {badge && <div className="absolute left-3 top-3">{badge}</div>}
      </div>

      {(prev || next) && (
        <nav aria-label="Otras obras" className="mt-2 flex items-center justify-between text-sm">
          {prev ? (
            <Link href={`/obras/${prev.id}`} className="inline-flex min-h-11 max-w-[48%] items-center gap-1 text-muted hover:text-foreground">
              <ChevronLeft size={18} aria-hidden /> <span className="truncate">{prev.title}</span>
            </Link>
          ) : <span />}
          {next ? (
            <Link href={`/obras/${next.id}`} className="inline-flex min-h-11 max-w-[48%] items-center gap-1 text-right text-muted hover:text-foreground">
              <span className="truncate">{next.title}</span> <ChevronRight size={18} aria-hidden />
            </Link>
          ) : <span />}
        </nav>
      )}

      {full && <Fullscreen src={src} alt={alt} onClose={close} />}
    </div>
  );
}
