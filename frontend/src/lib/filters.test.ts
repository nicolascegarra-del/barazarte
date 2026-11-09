import { describe, expect, it } from "vitest";
import { activeCount, parseFilters, toApiQuery, toHref } from "./filters";

describe("filters", () => {
  it("parseFilters_cuando_hay_valores_desconocidos_entonces_los_ignora", () => {
    const f = parseFilters({ precio: "99-1", tamano: "gigante", orden: "x", artista: "abc", disponibles: "si", tecnica: " Óleo " });

    expect(f).toEqual({ tecnica: "Óleo" });
  });

  it("toApiQuery_cuando_hay_rango_de_precio_abierto_entonces_solo_envia_el_minimo", () => {
    const q = new URLSearchParams(toApiQuery({ precio: "2000-", disponibles: "1", tamano: "grande", orden: "precio_asc" }));

    expect(q.get("min_price")).toBe("2000");
    expect(q.has("max_price")).toBe(false);
    expect(q.get("available")).toBe("true");
    expect(q.get("size")).toBe("grande");
    expect(q.get("sort")).toBe("precio_asc");
  });

  it("toHref_cuando_no_hay_filtros_entonces_devuelve_el_catalogo_limpio", () => {
    expect(toHref({})).toBe("/obras");
    expect(toHref({ tecnica: "Acuarela", precio: "0-500" })).toBe("/obras?tecnica=Acuarela&precio=0-500");
  });

  it("activeCount_cuando_solo_hay_orden_entonces_cuenta_cero", () => {
    expect(activeCount({ orden: "precio_desc" })).toBe(0);
    expect(activeCount({ orden: "precio_desc", tamano: "pequeno", disponibles: "1" })).toBe(2);
  });
});
