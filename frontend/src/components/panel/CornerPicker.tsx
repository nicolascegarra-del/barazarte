"use client";

import { useEffect, useRef, useState } from "react";
import { type Point, type Quad } from "@/lib/perspective";

const LABELS = ["superior izquierda", "superior derecha", "inferior derecha", "inferior izquierda"];
const LOUPE = 112; // px en pantalla
const LOUPE_ZOOM = 3;

interface Props {
  /** Foto de trabajo (ya girada). Las esquinas están en píxeles de esta imagen. */
  source: HTMLCanvasElement;
  quad: Quad;
  onChange: (q: Quad) => void;
  valid: boolean;
}

/**
 * Foto con 4 asas arrastrables que el artista coloca en las esquinas del cuadro.
 * Mientras se arrastra aparece una lupa sobre el dedo para ajustar con precisión.
 * Las asas también se mueven con las flechas del teclado (Mayús = pasos grandes).
 */
export function CornerPicker({ source, quad, onChange, valid }: Props) {
  const shown = useRef<HTMLCanvasElement>(null);
  const loupe = useRef<HTMLCanvasElement>(null);
  const frame = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState<number | null>(null);

  // Pinta la foto a un tamaño razonable para pantalla (no el original de varios megapíxeles).
  useEffect(() => {
    const c = shown.current;
    if (!c) return;
    const k = Math.min(1, 1400 / Math.max(source.width, source.height));
    c.width = Math.round(source.width * k);
    c.height = Math.round(source.height * k);
    c.getContext("2d")?.drawImage(source, 0, 0, c.width, c.height);
  }, [source]);

  // Lupa: recorte de la foto original alrededor del asa activa, ampliado.
  useEffect(() => {
    const c = loupe.current;
    if (!c || active === null || !frame.current) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    const screenToSource = source.width / frame.current.getBoundingClientRect().width;
    const region = (LOUPE / LOUPE_ZOOM) * screenToSource;
    const p = quad[active];
    ctx.fillStyle = "#faf8f4";
    ctx.fillRect(0, 0, LOUPE, LOUPE);
    ctx.drawImage(source, p.x - region / 2, p.y - region / 2, region, region, 0, 0, LOUPE, LOUPE);
    ctx.strokeStyle = "#8a6d2f";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(LOUPE / 2, 0); ctx.lineTo(LOUPE / 2, LOUPE);
    ctx.moveTo(0, LOUPE / 2); ctx.lineTo(LOUPE, LOUPE / 2);
    ctx.stroke();
  }, [active, quad, source]);

  const move = (i: number, p: Point) => {
    const next = [...quad] as Quad;
    next[i] = { x: Math.min(source.width, Math.max(0, p.x)), y: Math.min(source.height, Math.max(0, p.y)) };
    onChange(next);
  };

  function onPointerMove(e: React.PointerEvent<HTMLButtonElement>, i: number) {
    if (active !== i || !frame.current) return;
    const r = frame.current.getBoundingClientRect();
    move(i, { x: ((e.clientX - r.left) / r.width) * source.width, y: ((e.clientY - r.top) / r.height) * source.height });
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLButtonElement>, i: number) {
    const step = Math.max(1, source.width / 400) * (e.shiftKey ? 10 : 1);
    const d: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    const delta = d[e.key];
    if (!delta) return;
    e.preventDefault();
    setActive(i);
    move(i, { x: quad[i].x + delta[0], y: quad[i].y + delta[1] });
  }

  const pct = (p: Point) => ({ left: `${(p.x / source.width) * 100}%`, top: `${(p.y / source.height) * 100}%` });
  const points = quad.map((p) => `${p.x},${p.y}`).join(" ");
  // Rectángulo exterior + el cuadrilátero con regla evenodd = todo lo que queda fuera del cuadro se oscurece.
  const outside = `M0,0H${source.width}V${source.height}H0Z M${points.split(" ").join("L")}Z`;

  return (
    <div className="flex justify-center rounded-lg bg-[#ece8e0] p-3 md:p-5">
      {/* El marco se ajusta al tamaño de la foto; las asas se colocan en % sobre él */}
      <div ref={frame} className="relative inline-block max-w-full touch-none select-none">
        <canvas ref={shown} className="block h-auto max-h-[58vh] w-auto max-w-full shadow-md" aria-label="Foto de la obra" />
        <svg viewBox={`0 0 ${source.width} ${source.height}`} preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden>
          <path d={outside} fill="rgba(20,20,20,.5)" fillRule="evenodd" />
          <polygon points={points} fill="none" stroke={valid ? "#c9a24b" : "#c0392b"} strokeWidth={2} vectorEffect="non-scaling-stroke" />
        </svg>

        {quad.map((p, i) => (
          <button
            key={LABELS[i]}
            type="button"
            aria-label={`Esquina ${LABELS[i]}. Arrastra o usa las flechas.`}
            style={pct(p)}
            onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); setActive(i); }}
            onPointerMove={(e) => onPointerMove(e, i)}
            onPointerUp={() => setActive(null)}
            onPointerCancel={() => setActive(null)}
            onKeyDown={(e) => onKeyDown(e, i)}
            onBlur={() => setActive((a) => (a === i ? null : a))}
            className="absolute flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 cursor-grab items-center justify-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-[#8a6d2f]"
          >
            <span className={`block h-4 w-4 rounded-full border-2 border-white shadow ${valid ? "bg-[#c9a24b]" : "bg-[#c0392b]"}`} />
          </button>
        ))}

        {active !== null && (
          <canvas
            ref={loupe}
            width={LOUPE}
            height={LOUPE}
            aria-hidden
            style={{ ...pct(quad[active]), width: LOUPE, height: LOUPE }}
            // Sobre el dedo; si el asa está arriba del todo, la lupa pasa debajo
            className={`pointer-events-none absolute z-10 -translate-x-1/2 rounded-full border-2 border-white shadow-lg ${quad[active].y / source.height < 0.3 ? "translate-y-10" : "-translate-y-[150%]"}`}
          />
        )}
      </div>
    </div>
  );
}
