/**
 * Datos estructurados (schema.org) para buscadores. Se escapa "<" para que ningún texto de usuario
 * (título, descripción…) pueda cerrar la etiqueta <script> e inyectar HTML.
 */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  const json = JSON.stringify(data).replace(/</g, "\\u003c");
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: json }} />;
}
