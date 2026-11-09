/** Puente entre `perspective.ts` (puro) y los canvas del navegador. */
import { type Quad, fitMaxSide, quadSize, warpPerspective } from "./perspective";

function newCanvas(w: number, h: number): HTMLCanvasElement {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return c;
}

/** Copia de trabajo de la foto con el lado mayor limitado (las fotos de móvil pueden pesar 12+ MP). */
export function workingCanvas(img: HTMLImageElement, maxSide = 4096): HTMLCanvasElement {
  const { width, height } = fitMaxSide(img.naturalWidth, img.naturalHeight, maxSide);
  const c = newCanvas(width, height);
  c.getContext("2d")?.drawImage(img, 0, 0, width, height);
  return c;
}

/** Gira el canvas 90° en sentido horario (W×H → H×W). Coherente con `rotateQuad90`. */
export function rotateCanvas90(src: HTMLCanvasElement): HTMLCanvasElement {
  const c = newCanvas(src.height, src.width);
  const ctx = c.getContext("2d");
  if (!ctx) return c;
  ctx.translate(src.height, 0);
  ctx.rotate(Math.PI / 2);
  ctx.drawImage(src, 0, 0);
  return c;
}

/**
 * Recorta y endereza `quad` de `src` a un canvas rectangular cuyo lado mayor no pasa de `maxSide`.
 * Si el origen es mucho mayor que la salida se reduce antes de muestrear, para evitar aliasing (moiré).
 */
export function warpCanvas(src: HTMLCanvasElement, quad: Quad, maxSide: number): HTMLCanvasElement {
  const natural = quadSize(quad);
  const { width: outW, height: outH } = fitMaxSide(natural.width, natural.height, maxSide);

  let source = src;
  let q = quad;
  const k = Math.min(1, (2 * Math.max(outW, outH)) / Math.max(src.width, src.height));
  if (k < 1) {
    source = newCanvas(Math.max(1, Math.round(src.width * k)), Math.max(1, Math.round(src.height * k)));
    source.getContext("2d")?.drawImage(src, 0, 0, source.width, source.height);
    const sx = source.width / src.width, sy = source.height / src.height;
    q = quad.map((p) => ({ x: p.x * sx, y: p.y * sy })) as Quad;
  }

  const ctx = source.getContext("2d");
  if (!ctx) throw new Error("No se pudo leer la imagen");
  const raster = ctx.getImageData(0, 0, source.width, source.height);
  const warped = warpPerspective(raster, q, outW, outH);

  const out = newCanvas(outW, outH);
  out.getContext("2d")?.putImageData(new ImageData(warped.data as Uint8ClampedArray<ArrayBuffer>, outW, outH), 0, 0);
  return out;
}
