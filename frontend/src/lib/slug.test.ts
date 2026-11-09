import { describe, expect, it } from "vitest";
import { artworkPath, artworkSlug, parseArtworkId, slugify } from "./slug";

describe("slug", () => {
  it("slugify_cuando_hay_acentos_y_signos_entonces_deja_solo_letras_numeros_y_guiones", () => {
    expect(slugify("  Marea de ámbar, nº 3 (España)!  ")).toBe("marea-de-ambar-n-3-espana");
    expect(slugify("Niño")).toBe("nino");
  });

  it("slugify_cuando_el_titulo_es_muy_largo_entonces_lo_corta_sin_guion_final", () => {
    const s = slugify("a ".repeat(80));
    expect(s.length).toBeLessThanOrEqual(60);
    expect(s.endsWith("-")).toBe(false);
  });

  it("artworkSlug_cuando_el_titulo_no_tiene_letras_entonces_usa_solo_el_id", () => {
    expect(artworkSlug(7, "¿¡!?")).toBe("7");
    expect(artworkPath(7, "Bosque de noche")).toBe("/obras/7-bosque-de-noche");
  });

  it("parseArtworkId_cuando_hay_numero_inicial_entonces_lo_devuelve", () => {
    expect(parseArtworkId("7-bosque-de-noche")).toBe(7);
    expect(parseArtworkId("7")).toBe(7);
    expect(parseArtworkId("12-marea%20de")).toBe(12);
  });

  it("parseArtworkId_cuando_no_empieza_por_numero_o_esta_pegado_entonces_null", () => {
    expect(parseArtworkId("bosque")).toBeNull();
    expect(parseArtworkId("7abc")).toBeNull();
  });

  it("parseArtworkId_cuando_la_url_esta_mal_codificada_entonces_no_lanza", () => {
    expect(parseArtworkId("7-%E0%A4%A")).toBe(7);
    expect(parseArtworkId("%E0")).toBeNull();
  });
});
