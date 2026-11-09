"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Maximize, RotateCw, Undo2, Wand2 } from "lucide-react";
import { type Quad, defaultQuad, fullQuad, isValidQuad, rotateQuad90, shrinkQuad } from "@/lib/perspective";
import { rotateCanvas90, warpCanvas, workingCanvas } from "@/lib/perspective-canvas";
import { CornerPicker } from "./CornerPicker";

/** Ajustes de color y marca de agua (el recorte lo resuelve la corrección de perspectiva). */
interface Adjust {
  brightness: number;
  contrast: number;
  saturation: number;
  watermark: boolean;
  wmText: string;
  wmStyle: "esquina" | "diagonal"; // una firma en la esquina o texto repetido en diagonal
  wmOpacity: number; // %
}

const DEFAULTS: Adjust = {
  brightness: 100, contrast: 100, saturation: 100,
  watermark: false, wmText: "© Maripe · BarazArte", wmStyle: "esquina", wmOpacity: 45,
};

const PREVIEW_SIDE = 900; // px del lado mayor en la vista previa
const FINAL_SIDE = 2000; // px del lado mayor del archivo que se sube

/** Marca de agua grabada en los píxeles: la foto pública no se puede usar sin que aparezca la firma. */
function drawWatermark(ctx: CanvasRenderingContext2D, w: number, h: number, s: Adjust) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.filter = "none";
  ctx.globalAlpha = s.wmOpacity / 100;
  ctx.font = `500 ${Math.round(w * (s.wmStyle === "esquina" ? 0.04 : 0.05))}px Georgia, serif`;
  ctx.shadowColor = "rgba(0,0,0,.5)";
  ctx.shadowBlur = w * 0.004;
  ctx.fillStyle = "#ffffff";
  if (s.wmStyle === "esquina") {
    ctx.textAlign = "right";
    ctx.fillText(s.wmText, w - w * 0.03, h - h * 0.03);
  } else {
    ctx.textAlign = "center";
    ctx.translate(w / 2, h / 2);
    ctx.rotate(-Math.PI / 6);
    const step = w * 0.22;
    for (let y = -h; y <= h; y += step) for (let x = -w; x <= w; x += w * 0.7) ctx.fillText(s.wmText, x + ((y / step) % 2 ? w * 0.35 : 0), y);
  }
  ctx.globalAlpha = 1;
  ctx.shadowBlur = 0;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

/** Dibuja el cuadro ya recortado y enderezado con los ajustes de color y la marca de agua. */
function compose(target: HTMLCanvasElement, rect: HTMLCanvasElement, s: Adjust) {
  target.width = rect.width;
  target.height = rect.height;
  const ctx = target.getContext("2d");
  if (!ctx) return;
  ctx.filter = `brightness(${s.brightness}%) contrast(${s.contrast}%) saturate(${s.saturation}%)`;
  ctx.drawImage(rect, 0, 0);
  ctx.filter = "none";
  if (s.watermark && s.wmText.trim()) drawWatermark(ctx, target.width, target.height, s);
}

function Slider({
  label, value, min, max, step = 1, onChange, unit = "",
}: { label: string; value: number; min: number; max: number; step?: number; onChange: (v: number) => void; unit?: string }) {
  return (
    <label className="block">
      <span className="flex justify-between text-xs text-muted">
        {label}
        <span>{value}{unit}</span>
      </span>
      {/* h-11: zona táctil cómoda en móvil */}
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-11 w-full accent-[#8a6d2f]"
      />
    </label>
  );
}

const btn = "inline-flex min-h-11 items-center gap-2 border border-line px-3 text-sm";

/**
 * Editor de la foto del cuadro en dos etapas:
 * 1) Esquinas: el artista marca las 4 esquinas del cuadro y se corrige la perspectiva (sin pared alrededor).
 * 2) Ajustes: brillo, contraste, color y marca de agua sobre el cuadro ya recortado.
 * Devuelve un Blob WebP al pulsar "Continuar".
 */
export function ImageEditor({ file, onDone, onBack }: { file: File; onDone: (blob: Blob, previewUrl: string) => void; onBack: () => void }) {
  const [work, setWork] = useState<{ source: HTMLCanvasElement; quad: Quad } | null>(null);
  const [stage, setStage] = useState<"corners" | "adjust">("corners");
  const [rect, setRect] = useState<HTMLCanvasElement | null>(null);
  const [s, setS] = useState<Adjust>(DEFAULTS);
  const [compare, setCompare] = useState(false);
  const [trim, setTrim] = useState(0); // % que se recorta hacia dentro para quitar el último píxel de fondo
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const previewRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // `stale` evita que una carga anterior (React monta el efecto dos veces en desarrollo, o cambia `file`)
    // marque error o pise el estado cuando su URL ya fue revocada.
    let stale = false;
    const url = URL.createObjectURL(file);
    const el = new Image();
    el.onload = () => {
      if (stale) return;
      const source = workingCanvas(el);
      setWork({ source, quad: defaultQuad(source.width, source.height) });
    };
    el.onerror = () => {
      if (!stale) setLoadError(true);
    };
    el.src = url;
    return () => {
      stale = true;
      URL.revokeObjectURL(url);
    };
  }, [file]);

  useEffect(() => {
    if (stage === "adjust" && rect && previewRef.current) compose(previewRef.current, rect, compare ? DEFAULTS : s);
  }, [stage, rect, s, compare]);

  const set = <K extends keyof Adjust>(k: K, v: Adjust[K]) => setS((p) => ({ ...p, [k]: v }));

  if (loadError)
    return (
      <div role="alert" className="py-8 text-center text-sm">
        <p className="text-red-700">No se pudo abrir esta foto. Prueba con una en formato JPG, PNG o WebP.</p>
        <button type="button" onClick={onBack} className={`${btn} mt-4`}>Elegir otra foto</button>
      </div>
    );
  if (!work) return <p className="py-10 text-center text-sm text-muted">Cargando foto…</p>;

  const valid = isValidQuad(work.quad);

  function goAdjust(quad: Quad) {
    if (!work) return;
    setRect(warpCanvas(work.source, shrinkQuad(quad, trim / 100), PREVIEW_SIDE));
    setStage("adjust");
  }

  function changeTrim(v: number) {
    if (!work) return;
    setTrim(v);
    setRect(warpCanvas(work.source, shrinkQuad(work.quad, v / 100), PREVIEW_SIDE));
  }

  async function finish() {
    if (!work) return;
    setBusy(true);
    await new Promise((r) => setTimeout(r, 30)); // deja pintar el estado "Procesando…" antes del cálculo pesado
    const out = document.createElement("canvas");
    compose(out, warpCanvas(work.source, shrinkQuad(work.quad, trim / 100), FINAL_SIDE), s);
    out.toBlob((b) => {
      setBusy(false);
      if (b) onDone(b, URL.createObjectURL(b));
    }, "image/webp", 0.92);
  }

  if (stage === "corners")
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted">
          Arrastra cada punto hasta una esquina del cuadro. Al final solo se verá lo que quede dentro: marca el borde del
          lienzo o del marco, como prefieras.
        </p>
        <CornerPicker source={work.source} quad={work.quad} valid={valid} onChange={(quad) => setWork({ ...work, quad })} />
        {!valid && <p role="alert" className="text-sm text-red-700">Las esquinas se cruzan. Colócalas en orden, sin que las líneas se corten.</p>}

        <div className="flex flex-wrap gap-2">
          <button type="button" className={btn} onClick={() => setWork({ source: rotateCanvas90(work.source), quad: rotateQuad90(work.quad, work.source.height) })}>
            <RotateCw size={16} aria-hidden /> Girar foto
          </button>
          <button type="button" className={btn} onClick={() => setWork({ ...work, quad: defaultQuad(work.source.width, work.source.height) })}>
            <Undo2 size={16} aria-hidden /> Restablecer esquinas
          </button>
          <button type="button" className={btn} onClick={() => { const quad = fullQuad(work.source.width, work.source.height); setWork({ ...work, quad }); goAdjust(quad); }}>
            <Maximize size={16} aria-hidden /> Usar foto completa
          </button>
        </div>

        <div className="sticky bottom-20 z-10 flex gap-3 bg-background py-3 md:static">
          <button type="button" onClick={onBack} className="min-h-12 flex-1 border border-line px-5 text-sm md:flex-none">Cambiar foto</button>
          <button
            type="button" disabled={!valid} onClick={() => goAdjust(work.quad)}
            className="min-h-12 flex-1 bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background disabled:opacity-50 md:flex-none"
          >
            Recortar
          </button>
        </div>
      </div>
    );

  return (
    <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_320px]">
      {/* En móvil la vista previa queda fija arriba mientras se mueven los controles */}
      <div className="sticky top-0 z-10 bg-background pb-2 md:static">
        <div className="flex justify-center rounded-lg bg-[#ece8e0] p-3">
          <canvas ref={previewRef} aria-label="Vista previa del cuadro recortado" className="max-h-[38vh] w-auto max-w-full shadow-md md:max-h-[60vh]" />
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setStage("corners")} className={btn}>
            <ArrowLeft size={16} aria-hidden /> Esquinas
          </button>
          <button type="button" onClick={() => setS((p) => ({ ...p, brightness: 108, contrast: 112, saturation: 108 }))} className={btn}>
            <Wand2 size={16} aria-hidden /> Mejorar
          </button>
          <button
            type="button" onPointerDown={() => setCompare(true)} onPointerUp={() => setCompare(false)} onPointerLeave={() => setCompare(false)}
            className={btn}
          >
            <Undo2 size={16} aria-hidden /> Ver original
          </button>
        </div>

        <div>
          <Slider label="Afinar bordes" value={trim} min={0} max={4} step={0.25} unit="%" onChange={changeTrim} />
          <p className="text-[11px] text-muted">Si ves una línea de pared en el borde, sube un poco para recortarla.</p>
        </div>
        <Slider label="Brillo" value={s.brightness} min={60} max={150} unit="%" onChange={(v) => set("brightness", v)} />
        <Slider label="Contraste" value={s.contrast} min={60} max={150} unit="%" onChange={(v) => set("contrast", v)} />
        <Slider label="Color" value={s.saturation} min={0} max={200} unit="%" onChange={(v) => set("saturation", v)} />

        <fieldset className="space-y-2 border-t border-line pt-4">
          <label className="flex min-h-11 items-center gap-3 text-sm">
            <input type="checkbox" checked={s.watermark} onChange={(e) => set("watermark", e.target.checked)} className="h-5 w-5 accent-[#8a6d2f]" />
            Proteger con marca de agua
          </label>
          {s.watermark && (
            <>
              <input
                value={s.wmText} maxLength={40} onChange={(e) => set("wmText", e.target.value)} aria-label="Texto de la marca de agua"
                className="min-h-11 w-full rounded-md border border-line bg-white px-3 text-base md:text-sm"
              />
              <div className="flex gap-2">
                {(["esquina", "diagonal"] as const).map((v) => (
                  <button
                    key={v} type="button" aria-pressed={s.wmStyle === v} onClick={() => set("wmStyle", v)}
                    className={`min-h-11 flex-1 border px-3 text-sm ${s.wmStyle === v ? "border-gold text-gold" : "border-line"}`}
                  >
                    {v === "esquina" ? "Firma en esquina" : "Repetida en diagonal"}
                  </button>
                ))}
              </div>
              <Slider label="Intensidad" value={s.wmOpacity} min={15} max={80} unit="%" onChange={(v) => set("wmOpacity", v)} />
              <p className="text-xs text-muted">La marca se graba en la foto que verán los visitantes.</p>
            </>
          )}
        </fieldset>

        <button type="button" onClick={() => setS(DEFAULTS)} className="text-xs text-muted underline">Restablecer ajustes</button>
      </div>

      <div className="sticky bottom-20 z-10 flex gap-3 bg-background py-3 md:static md:col-span-2 md:bottom-0">
        <button type="button" onClick={onBack} className="min-h-12 flex-1 border border-line px-5 text-sm md:flex-none">Cambiar foto</button>
        <button
          type="button" onClick={finish} disabled={busy}
          className="min-h-12 flex-1 bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background disabled:opacity-60 md:flex-none"
        >
          {busy ? "Procesando…" : "Continuar"}
        </button>
      </div>
    </div>
  );
}
