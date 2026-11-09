/**
 * Corrección de perspectiva para fotos de cuadros: convierte el cuadrilátero que el artista marca sobre la foto
 * en un rectángulo perfecto (sin pared alrededor). Funciones puras, sin DOM, para poder probarlas con Vitest.
 *
 * Convención de coordenadas: continuas, en píxeles de la imagen de origen; el píxel i cubre [i, i+1).
 */
export interface Point { x: number; y: number }
/** Esquinas en este orden: arriba-izquierda, arriba-derecha, abajo-derecha, abajo-izquierda. */
export type Quad = [Point, Point, Point, Point];
/** Imagen RGBA 8 bits (mismo formato que ImageData, pero sin depender del DOM). */
export interface Raster { data: Uint8ClampedArray; width: number; height: number }

export const dist = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

/** Rectángulo inicial inset (fracción del lado) dentro de una imagen de w×h. */
export function defaultQuad(w: number, h: number, inset = 0.08): Quad {
  const x0 = w * inset, x1 = w * (1 - inset), y0 = h * inset, y1 = h * (1 - inset);
  return [{ x: x0, y: y0 }, { x: x1, y: y0 }, { x: x1, y: y1 }, { x: x0, y: y1 }];
}

/** Cuadrilátero que ocupa toda la imagen (opción "usar foto completa"). */
export const fullQuad = (w: number, h: number): Quad => defaultQuad(w, h, 0);

/**
 * Tamaño natural del rectángulo resultante: el lado mayor de cada pareja de lados opuestos,
 * para no perder resolución en el lado más cercano a la cámara.
 */
export function quadSize(q: Quad): { width: number; height: number } {
  return {
    width: Math.max(dist(q[0], q[1]), dist(q[3], q[2])),
    height: Math.max(dist(q[0], q[3]), dist(q[1], q[2])),
  };
}

/** Escala (width, height) para que el lado mayor no pase de `maxSide`, sin ampliar. Mínimo 1 px. */
export function fitMaxSide(width: number, height: number, maxSide: number) {
  const k = Math.min(1, maxSide / Math.max(width, height));
  return { width: Math.max(1, Math.round(width * k)), height: Math.max(1, Math.round(height * k)) };
}

const cross = (o: Point, a: Point, b: Point) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);

/** Un cuadrilátero sirve si es convexo (esquinas en orden, sin cruzarse) y tiene área apreciable. */
export function isValidQuad(q: Quad, minSide = 8): boolean {
  const signs = [0, 1, 2, 3].map((i) => Math.sign(cross(q[i], q[(i + 1) % 4], q[(i + 2) % 4])));
  if (signs.some((s) => s === 0) || !signs.every((s) => s === signs[0])) return false;
  const { width, height } = quadSize(q);
  return width >= minSide && height >= minSide;
}

/** Acerca las 4 esquinas al centro (fracción `k` de la distancia): quita el último píxel de pared del borde. */
export function shrinkQuad(q: Quad, k: number): Quad {
  const cx = (q[0].x + q[1].x + q[2].x + q[3].x) / 4;
  const cy = (q[0].y + q[1].y + q[2].y + q[3].y) / 4;
  return q.map((p) => ({ x: p.x + (cx - p.x) * k, y: p.y + (cy - p.y) * k })) as Quad;
}

/** Giro de 90° en sentido horario de la imagen (de W×H a H×W): reasigna y recoloca las esquinas. */
export function rotateQuad90(q: Quad, oldHeight: number): Quad {
  const r = (p: Point): Point => ({ x: oldHeight - p.y, y: p.x });
  // La esquina que era arriba-izquierda pasa a arriba-derecha, etc.
  return [r(q[3]), r(q[0]), r(q[1]), r(q[2])];
}

/** Resuelve A·x = b (n×n) por eliminación gaussiana con pivote parcial. Devuelve null si es singular. */
function solveLinear(a: number[][], b: number[]): number[] | null {
  const n = b.length;
  const m = a.map((row, i) => [...row, b[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(m[r][c]) > Math.abs(m[p][c])) p = r;
    if (Math.abs(m[p][c]) < 1e-12) return null;
    [m[c], m[p]] = [m[p], m[c]];
    for (let r = c + 1; r < n; r++) {
      const f = m[r][c] / m[c][c];
      for (let k = c; k <= n; k++) m[r][k] -= f * m[c][k];
    }
  }
  const x = new Array<number>(n).fill(0);
  for (let r = n - 1; r >= 0; r--) {
    let s = m[r][n];
    for (let k = r + 1; k < n; k++) s -= m[r][k] * x[k];
    x[r] = s / m[r][r];
  }
  return x;
}

/** Homografía 3×3 (h8 = 1) que lleva cada punto `from[i]` a `to[i]`. */
export function computeHomography(from: Point[], to: Point[]): number[] | null {
  const a: number[][] = [];
  const b: number[] = [];
  for (let i = 0; i < 4; i++) {
    const { x, y } = from[i];
    const { x: u, y: v } = to[i];
    a.push([x, y, 1, 0, 0, 0, -u * x, -u * y]);
    b.push(u);
    a.push([0, 0, 0, x, y, 1, -v * x, -v * y]);
    b.push(v);
  }
  const h = solveLinear(a, b);
  return h ? [...h, 1] : null;
}

export function applyHomography(h: number[], x: number, y: number): Point {
  const w = h[6] * x + h[7] * y + h[8];
  return { x: (h[0] * x + h[1] * y + h[2]) / w, y: (h[3] * x + h[4] * y + h[5]) / w };
}

/**
 * Endereza el cuadrilátero `quad` de `src` a un rectángulo outW×outH.
 * Mapeo inverso (por cada píxel de salida se busca su origen) con interpolación bilineal.
 */
export function warpPerspective(src: Raster, quad: Quad, outW: number, outH: number): Raster {
  const rect: Point[] = [{ x: 0, y: 0 }, { x: outW, y: 0 }, { x: outW, y: outH }, { x: 0, y: outH }];
  const h = computeHomography(rect, quad);
  if (!h) throw new Error("Las esquinas no forman un cuadrilátero válido");

  const out = new Uint8ClampedArray(outW * outH * 4);
  const { data, width: sw, height: sh } = src;
  const maxX = sw - 1, maxY = sh - 1;

  for (let y = 0; y < outH; y++) {
    for (let x = 0; x < outW; x++) {
      const w = h[6] * (x + 0.5) + h[7] * (y + 0.5) + h[8];
      // -0.5: el centro del píxel i está en i + 0.5
      const sx = Math.min(maxX, Math.max(0, (h[0] * (x + 0.5) + h[1] * (y + 0.5) + h[2]) / w - 0.5));
      const sy = Math.min(maxY, Math.max(0, (h[3] * (x + 0.5) + h[4] * (y + 0.5) + h[5]) / w - 0.5));
      const x0 = Math.floor(sx), y0 = Math.floor(sy);
      const x1 = Math.min(maxX, x0 + 1), y1 = Math.min(maxY, y0 + 1);
      const fx = sx - x0, fy = sy - y0;
      const i00 = (y0 * sw + x0) * 4, i10 = (y0 * sw + x1) * 4, i01 = (y1 * sw + x0) * 4, i11 = (y1 * sw + x1) * 4;
      const o = (y * outW + x) * 4;
      for (let c = 0; c < 4; c++) {
        const top = data[i00 + c] * (1 - fx) + data[i10 + c] * fx;
        const bottom = data[i01 + c] * (1 - fx) + data[i11 + c] * fx;
        out[o + c] = top * (1 - fy) + bottom * fy;
      }
    }
  }
  return { data: out, width: outW, height: outH };
}
