import Link from "next/link";
import { Fill, LegalPage, LegalTable } from "@/components/LegalPage";

export const metadata = { title: "Política de privacidad · BarazArte", alternates: { canonical: "/legal/privacidad" } };

export default function Privacidad() {
  return (
    <LegalPage title="Política de privacidad" updated="9 de noviembre de 2026" current="/legal/privacidad">
      <p>
        Esta política explica qué datos personales trata BarazArte, para qué y qué derechos tienes, conforme al
        Reglamento (UE) 2016/679 (RGPD) y a la Ley Orgánica 3/2018 (LOPDGDD).
      </p>

      <h2>Responsable del tratamiento</h2>
      <ul>
        <li>Responsable: <Fill>nombre y apellidos o razón social</Fill></li>
        <li>NIF/CIF: <Fill>NIF o CIF</Fill></li>
        <li>Domicilio: <Fill>dirección postal completa</Fill></li>
        <li>Email para cuestiones de privacidad: <Fill>email de contacto</Fill></li>
      </ul>

      <h2>Qué datos tratamos y para qué</h2>
      <LegalTable>
        <thead>
          <tr><th>Quién</th><th>Datos</th><th>Finalidad</th><th>Base legal</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Personas que contactan con un artista</td>
            <td>Nombre, email, teléfono (opcional) y mensaje</td>
            <td>Hacer llegar la consulta al artista para que pueda responderte, y enviarte una confirmación</td>
            <td>Tu consentimiento al enviar el formulario (art. 6.1.a RGPD)</td>
          </tr>
          <tr>
            <td>Artistas</td>
            <td>Nombre artístico, email, contraseña (cifrada), obras y fotografías</td>
            <td>Gestionar tu cuenta y publicar tus obras</td>
            <td>Ejecución del servicio que solicitas al registrarte (art. 6.1.b RGPD)</td>
          </tr>
          <tr>
            <td>Artistas que activan avisos</td>
            <td>Identificador técnico de notificaciones del dispositivo</td>
            <td>Avisarte en el móvil cuando recibes una consulta</td>
            <td>Tu consentimiento al activar los avisos; puedes retirarlo desactivándolos</td>
          </tr>
          <tr>
            <td>Visitantes</td>
            <td>Ninguno personal: solo se cuenta el número de visitas por día y por obra, sin cookies ni dirección IP</td>
            <td>Estadísticas agregadas de la galería</td>
            <td>No hay tratamiento de datos personales</td>
          </tr>
        </tbody>
      </LegalTable>

      <h2>A quién se comunican tus datos</h2>
      <ul>
        <li>
          Si envías una consulta, tus datos se envían al artista de la obra por la que preguntas. A partir de ahí, el
          artista los trata por su cuenta para responderte y acordar la venta.
        </li>
        <li>
          Proveedores que nos prestan servicio y tratan los datos solo por cuenta de BarazArte: alojamiento del servidor
          (<Fill>proveedor de hosting, p. ej. Contabo GmbH, Alemania</Fill>) y envío de emails
          (<Fill>proveedor de correo</Fill>). Los avisos al móvil pasan por el servicio de notificaciones del fabricante del
          navegador (Google, Apple o Mozilla) solo con el texto del aviso.
        </li>
        <li>No se venden ni ceden datos a terceros con fines comerciales.</li>
      </ul>

      <h2>Cuánto tiempo los conservamos</h2>
      <ul>
        <li>Consultas: mientras el artista mantenga su cuenta y, como máximo, <Fill>plazo, p. ej. 2 años</Fill>.</li>
        <li>Cuentas de artistas: mientras la cuenta esté activa; al darla de baja se eliminan sus datos y obras.</li>
        <li>Identificadores de avisos: hasta que los desactives o el dispositivo deje de aceptarlos.</li>
      </ul>

      <h2>Tus derechos</h2>
      <p>
        Puedes ejercer tus derechos de acceso, rectificación, supresión, oposición, limitación del tratamiento y
        portabilidad, así como retirar tu consentimiento en cualquier momento, escribiendo a <Fill>email de contacto</Fill>.
        Si consideras que no hemos atendido correctamente tu solicitud, puedes reclamar ante la Agencia Española de
        Protección de Datos (aepd.es).
      </p>

      <h2>Seguridad</h2>
      <p>
        La web funciona siempre con conexión cifrada (HTTPS), las contraseñas se guardan cifradas y nunca se pueden leer,
        y el acceso al panel está restringido a cada artista.
      </p>

      <p>
        Sobre las cookies, consulta la <Link href="/legal/cookies" className="underline">política de cookies</Link>.
      </p>
    </LegalPage>
  );
}
