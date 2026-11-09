import { LegalPage, LegalTable } from "@/components/LegalPage";

export const metadata = { title: "Política de cookies · BarazArte", alternates: { canonical: "/legal/cookies" } };

export default function Cookies() {
  return (
    <LegalPage title="Política de cookies" updated="9 de noviembre de 2026" current="/legal/cookies">
      <p>
        BarazArte <strong>no usa cookies de publicidad, de analítica ni de terceros</strong>. Las visitas a la galería se
        cuentan de forma anónima, sin cookies y sin guardar tu dirección IP. Por eso no te mostramos un banner de cookies.
      </p>

      <h2>Cookies técnicas que sí usamos</h2>
      <p>
        Solo se usa una cookie, y únicamente si eres artista e inicias sesión en tu panel. Es estrictamente necesaria para
        mantener tu sesión abierta de forma segura, por lo que está exenta de consentimiento (artículo 22.2 de la LSSI-CE).
      </p>
      <LegalTable>
        <thead>
          <tr><th>Nombre</th><th>Finalidad</th><th>Duración</th><th>Tipo</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>refresh_token</td>
            <td>Mantener la sesión del artista en su panel</td>
            <td>7 días o hasta cerrar sesión</td>
            <td>Propia, técnica, inaccesible para JavaScript</td>
          </tr>
        </tbody>
      </LegalTable>

      <h2>Otros almacenamientos del navegador</h2>
      <p>
        Si eres artista y activas los avisos en el móvil, el navegador guarda un pequeño programa (service worker) para
        poder mostrarte las notificaciones. Puedes eliminarlo desactivando los avisos o borrando los datos del sitio en los
        ajustes de tu navegador.
      </p>

      <h2>Cómo gestionarlas</h2>
      <p>
        Puedes bloquear o eliminar las cookies desde los ajustes de tu navegador. Si bloqueas la cookie de sesión, podrás
        ver la galería con normalidad, pero no podrás iniciar sesión en el panel de artista.
      </p>
    </LegalPage>
  );
}
