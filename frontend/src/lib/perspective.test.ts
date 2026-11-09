import { describe, expect, it } from "vitest";
import {
  type Point,
  type Quad,
  type Raster,
  applyHomography,
  computeHomography,
  defaultQuad,
  fitMaxSide,
  fullQuad,
  isValidQuad,
  quadSize,
  rotateQuad90,
  shrinkQuad,
  warpPerspective,
} from "./perspective";

const px = (r: Raster, x: number, y: number) => {
  const i = (y * r.width + x) * 4;
  return [r.data[i], r.data[i + 1], r.data[i + 2]];
};

/** Imagen sintética: fondo azul ("pared") con un cuadrilátero rojo ("cuadro") visto en perspectiva. */
function paintingOnWall(): { raster: Raster; quad: Quad } {
  const width = 400, height = 300;
  const poly: Quad = [{ x: 90, y: 60 }, { x: 310, y: 40 }, { x: 340, y: 250 }, { x: 70, y: 230 }];
  const sign = (a: Point, b: Point, p: Point) => (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
  const inside = (p: Point) => poly.every((a, i) => sign(a, poly[(i + 1) % 4], p) > 0);
  const data = new Uint8ClampedArray(width * height * 4);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const o = (y * width + x) * 4;
      const red = inside({ x: x + 0.5, y: y + 0.5 });
      data[o] = red ? 200 : 20;
      data[o + 1] = red ? 30 : 40;
      data[o + 2] = red ? 30 : 200;
      data[o + 3] = 255;
    }
  }
  // Un par de píxeles hacia dentro del cuadro, para no mezclar con el borde.
  const k = 0.02;
  const cx = poly.reduce((s, p) => s + p.x, 0) / 4, cy = poly.reduce((s, p) => s + p.y, 0) / 4;
  const quad = poly.map((p) => ({ x: p.x + (cx - p.x) * k, y: p.y + (cy - p.y) * k })) as Quad;
  return { raster: { data, width, height }, quad };
}

describe("perspective", () => {
  it("computeHomography_cuando_se_mapea_un_rectangulo_a_un_cuadrilatero_entonces_las_esquinas_coinciden", () => {
    const rect: Point[] = [{ x: 0, y: 0 }, { x: 200, y: 0 }, { x: 200, y: 100 }, { x: 0, y: 100 }];
    const quad: Quad = [{ x: 30, y: 20 }, { x: 180, y: 10 }, { x: 210, y: 140 }, { x: 10, y: 120 }];

    const h = computeHomography(rect, quad)!;

    rect.forEach((p, i) => {
      const r = applyHomography(h, p.x, p.y);
      expect(Math.abs(r.x - quad[i].x)).toBeLessThan(0.5);
      expect(Math.abs(r.y - quad[i].y)).toBeLessThan(0.5);
    });
  });

  it("warpPerspective_cuando_el_cuadrilatero_es_toda_la_imagen_entonces_devuelve_la_misma_imagen", () => {
    const width = 20, height = 10;
    const data = new Uint8ClampedArray(width * height * 4);
    for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) data.set([x * 12, y * 25, 100, 255], (y * width + x) * 4);

    const out = warpPerspective({ data, width, height }, fullQuad(width, height), width, height);

    for (let i = 0; i < data.length; i++) expect(Math.abs(out.data[i] - data[i])).toBeLessThanOrEqual(1);
  });

  it("warpPerspective_cuando_se_marcan_las_esquinas_del_cuadro_entonces_no_queda_nada_de_pared", () => {
    const { raster, quad } = paintingOnWall();
    const { width, height } = quadSize(quad);

    const out = warpPerspective(raster, quad, Math.round(width), Math.round(height));

    // Todos los píxeles del borde de la salida, incluidas las cuatro esquinas, son del cuadro (rojo), no de la pared (azul).
    for (let x = 0; x < out.width; x++) for (const y of [0, out.height - 1]) expect(px(out, x, y)).toEqual([200, 30, 30]);
    for (let y = 0; y < out.height; y++) for (const x of [0, out.width - 1]) expect(px(out, x, y)).toEqual([200, 30, 30]);
    expect(px(out, Math.floor(out.width / 2), Math.floor(out.height / 2))).toEqual([200, 30, 30]);
  });

  it("isValidQuad_cuando_las_esquinas_estan_en_orden_entonces_es_valido", () => {
    expect(isValidQuad(defaultQuad(400, 300))).toBe(true);
  });

  it("isValidQuad_cuando_las_esquinas_se_cruzan_entonces_no_es_valido", () => {
    const [a, b, c, d] = defaultQuad(400, 300);

    expect(isValidQuad([a, c, b, d])).toBe(false);
  });

  it("isValidQuad_cuando_las_esquinas_son_colineales_entonces_no_es_valido", () => {
    const line: Quad = [{ x: 0, y: 0 }, { x: 100, y: 0 }, { x: 200, y: 0 }, { x: 300, y: 0 }];

    expect(isValidQuad(line)).toBe(false);
  });

  it("isValidQuad_cuando_es_diminuto_entonces_no_es_valido", () => {
    expect(isValidQuad([{ x: 0, y: 0 }, { x: 2, y: 0 }, { x: 2, y: 2 }, { x: 0, y: 2 }])).toBe(false);
  });

  it("quadSize_cuando_los_lados_opuestos_difieren_entonces_usa_el_mayor_de_cada_pareja", () => {
    const q: Quad = [{ x: 0, y: 0 }, { x: 100, y: 0 }, { x: 120, y: 80 }, { x: -20, y: 80 }];

    const { width, height } = quadSize(q);

    expect(width).toBeCloseTo(140);
    expect(height).toBeCloseTo(Math.hypot(20, 80));
  });

  it("fitMaxSide_cuando_supera_el_maximo_entonces_reduce_manteniendo_proporcion_y_nunca_amplia", () => {
    expect(fitMaxSide(4000, 3000, 2000)).toEqual({ width: 2000, height: 1500 });
    expect(fitMaxSide(500, 300, 2000)).toEqual({ width: 500, height: 300 });
  });

  it("shrinkQuad_cuando_se_afina_entonces_las_esquinas_se_acercan_al_centro_y_el_orden_se_mantiene", () => {
    const q = defaultQuad(400, 300, 0);

    const s = shrinkQuad(q, 0.1);

    expect(s[0].x).toBeCloseTo(20);
    expect(s[0].y).toBeCloseTo(15);
    expect(s[2].x).toBeCloseTo(380);
    expect(isValidQuad(s)).toBe(true);
    expect(shrinkQuad(q, 0)).toEqual(q);
  });

  it("rotateQuad90_cuando_se_gira_cuatro_veces_entonces_vuelve_al_cuadrilatero_original", () => {
    let q: Quad = [{ x: 10, y: 20 }, { x: 300, y: 30 }, { x: 290, y: 200 }, { x: 15, y: 190 }];
    const original = q;
    let w = 400, h = 250;
    for (let i = 0; i < 4; i++) {
      q = rotateQuad90(q, h);
      [w, h] = [h, w];
    }

    q.forEach((p, i) => {
      expect(p.x).toBeCloseTo(original[i].x);
      expect(p.y).toBeCloseTo(original[i].y);
    });
  });

  it("rotateQuad90_cuando_se_gira_entonces_la_esquina_arriba_izquierda_pasa_a_arriba_derecha", () => {
    const q = defaultQuad(400, 250, 0);

    const r = rotateQuad90(q, 250);

    // La imagen rotada mide 250×400: la antigua esquina (0,0) queda en (250,0), arriba-derecha.
    expect(r[1].x).toBeCloseTo(250);
    expect(r[1].y).toBeCloseTo(0);
  });
});
