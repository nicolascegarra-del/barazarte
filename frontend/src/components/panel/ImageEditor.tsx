"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RotateCw, Wand2, Undo2 } from "lucide-react";

export interface EditSettings {
  quarter: number; // giros de 90°
  angle: number; // enderezado fino, grados
  zoom: number;
  aspect: number | null; // ancho/alto; null = original
  brightness: number;
  contrast: number;
  saturation: number;
  panX: number; // desplazamiento en fracción del lienzo
  panY: number;
  watermark: boolean;
  wmText: string;
  wmStyle: "esquina" | "diagonal"; // una firma en la esquina o texto repetido en diagonal
  wmOpacity: number; // %
}

const DEFAULTS: EditSettings = {
  quarter: 0, angle: 0, zoom: 1, aspect: null, brightness: 100, contrast: 100, saturation: 100, panX: 0, panY: 0,
  watermark: false, wmText: "© Maripe · BarazArte", wmStyle: "esquina", wmOpacity: 45,
};

/** Marca de agua grabada en los píxeles: la foto pública no se puede usar sin que aparezca la firma. */
function drawWatermark(ctx: CanvasRenderingContext2D, w: number, h: number, s: EditSettings) {
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
    for (let y = -h; y <= h; y += step) for (let x = -w; x <= w; x += w * 0.7) ctx.fillText(s.wmText, x + (y / step % 2 ? w * 0.35 : 0), y);
  }
  ctx.globalAlpha = 1;
  ctx.shadowBlur = 0;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

const ASPECTS: { label: string; value: number | null }[] = [
  { label: "Original", value: null },
  { label: "4:5", value: 4 / 5 },
  { label: "1:1", value: 1 },
  { label: "3:4", value: 3 / 4 },
];

/** Dibuja la imagen con las correcciones en un canvas de ancho `outW`. Sirve para la vista previa y el resultado final. */
function render(canvas: HTMLCanvasElement, img: HTMLImageElement, s: EditSettings, outW: number) {
  const odd = s.quarter % 2 !== 0;
  const rw = odd ? img.naturalHeight : img.naturalWidth;
  const rh = odd ? img.naturalWidth : img.naturalHeight;
  const ar = s.aspect ?? rw / rh;
  const outH = Math.round(outW / ar);
  canvas.width = outW;
  canvas.height = outH;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const rad = (s.angle * Math.PI) / 180;
  // Factor extra para que al enderezar no queden esquinas vacías.
  const cover = Math.cos(Math.abs(rad)) + Math.sin(Math.abs(rad)) * Math.max(ar, 1 / ar);
  const scale = Math.max(outW / rw, outH / rh) * s.zoom * cover;

  ctx.fillStyle = "#faf8f4";
  ctx.fillRect(0, 0, outW, outH);
  ctx.filter = `brightness(${s.brightness}%) contrast(${s.contrast}%) saturate(${s.saturation}%)`;
  ctx.translate(outW / 2 + s.panX * outW, outH / 2 + s.panY * outH);
  ctx.rotate((s.quarter * Math.PI) / 2 + rad);
  ctx.scale(scale, scale);
  ctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2);
  if (s.watermark && s.wmText.trim()) drawWatermark(ctx, outW, outH, s);
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

/**
 * Editor de la foto del cuadro: recorte con proporciones, giro, enderezado, zoom, brillo, contraste y color.
 * Arrastrar sobre la imagen la desplaza. Devuelve un Blob WebP al pulsar "Continuar".
 */
export function ImageEditor({ file, onDone, onBack }: { file: File; onDone: (blob: Blob, previewUrl: string) => void; onBack: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [img, setImg] = useState<HTMLImageElement | null>(null);
  const [s, setS] = useState<EditSettings>(DEFAULTS);
  const [compare, setCompare] = useState(false);
  const drag = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    const el = new Image();
    el.onload = () => setImg(el);
    el.src = url;
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (img && canvasRef.current) render(canvasRef.current, img, compare ? DEFAULTS : s, 720);
  }, [img, s, compare]);

  const set = useCallback(<K extends keyof EditSettings>(k: K, v: EditSettings[K]) => setS((p) => ({ ...p, [k]: v })), []);

  function onPointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    e.currentTarget.setPointerCapture(e.pointerId);
    drag.current = { x: e.clientX, y: e.clientY };
  }
  function onPointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!drag.current) return;
    const r = e.currentTarget.getBoundingClientRect();
    const dx = (e.clientX - drag.current.x) / r.width;
    const dy = (e.clientY - drag.current.y) / r.height;
    drag.current = { x: e.clientX, y: e.clientY };
    setS((p) => ({ ...p, panX: p.panX + dx, panY: p.panY + dy }));
  }

  function finish() {
    if (!img) return;
    const out = document.createElement("canvas");
    render(out, img, s, 2000);
    out.toBlob((b) => b && onDone(b, URL.createObjectURL(b)), "image/webp", 0.92);
  }

  const auto = () => setS((p) => ({ ...p, brightness: 108, contrast: 112, saturation: 108 }));

  return (
    <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_320px]">
      {/* En móvil la vista previa queda fija arriba mientras se mueven los controles */}
      <div className="sticky top-0 z-10 bg-background pb-2 md:static">
        <div className="flex justify-center rounded-lg bg-[#ece8e0] p-3">
          <canvas
            ref={canvasRef}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={() => (drag.current = null)}
            aria-label="Vista previa de la foto. Arrastra para mover."
            className="max-h-[38vh] w-auto md:max-h-[60vh] max-w-full touch-none cursor-grab shadow-md"
          />
        </div>
        <p className="mt-2 text-center text-xs text-muted">Arrastra la imagen para encuadrarla</p>
      </div>

      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => set("quarter", (s.quarter + 1) % 4)} className="inline-flex min-h-11 items-center gap-2 border border-line px-3 text-sm">
            <RotateCw size={16} aria-hidden /> Girar
          </button>
          <button type="button" onClick={auto} className="inline-flex min-h-11 items-center gap-2 border border-line px-3 text-sm">
            <Wand2 size={16} aria-hidden /> Mejorar
          </button>
          <button type="button" onPointerDown={() => setCompare(true)} onPointerUp={() => setCompare(false)} onPointerLeave={() => setCompare(false)} className="inline-flex min-h-11 items-center gap-2 border border-line px-3 text-sm">
            <Undo2 size={16} aria-hidden /> Ver original
          </button>
        </div>

        <fieldset>
          <legend className="mb-1 text-xs text-muted">Proporción</legend>
          <div className="flex flex-wrap gap-2">
            {ASPECTS.map((a) => (
              <button
                key={a.label} type="button" aria-pressed={s.aspect === a.value} onClick={() => set("aspect", a.value)}
                className={`min-h-11 min-w-14 border px-3 text-sm ${s.aspect === a.value ? "border-gold text-gold" : "border-line"}`}
              >
                {a.label}
              </button>
            ))}
          </div>
        </fieldset>

        <Slider label="Enderezar" value={s.angle} min={-15} max={15} step={0.5} unit="°" onChange={(v) => set("angle", v)} />
        <Slider label="Zoom" value={s.zoom} min={1} max={3} step={0.05} unit="×" onChange={(v) => set("zoom", v)} />
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
                  <button key={v} type="button" aria-pressed={s.wmStyle === v} onClick={() => set("wmStyle", v)}
                    className={`min-h-11 flex-1 border px-3 text-sm ${s.wmStyle === v ? "border-gold text-gold" : "border-line"}`}>
                    {v === "esquina" ? "Firma en esquina" : "Repetida en diagonal"}
                  </button>
                ))}
              </div>
              <Slider label="Intensidad" value={s.wmOpacity} min={15} max={80} unit="%" onChange={(v) => set("wmOpacity", v)} />
              <p className="text-xs text-muted">La marca se graba en la foto que verán los visitantes.</p>
            </>
          )}
        </fieldset>

        <button type="button" onClick={() => setS(DEFAULTS)} className="text-xs text-muted underline">Restablecer todo</button>
      </div>

      <div className="sticky bottom-20 z-10 flex gap-3 bg-background py-3 md:static md:col-span-2 md:bottom-0">
        <button type="button" onClick={onBack} className="min-h-12 flex-1 border border-line px-5 text-sm md:flex-none">Cambiar foto</button>
        <button type="button" onClick={finish} disabled={!img} className="min-h-12 flex-1 bg-foreground px-6 text-xs uppercase tracking-[0.18em] text-background disabled:opacity-50 md:flex-none">
          Continuar
        </button>
      </div>
    </div>
  );
}
