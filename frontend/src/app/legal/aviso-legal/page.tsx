import { Fill, LegalPage } from "@/components/LegalPage";

export const metadata = { title: "Aviso legal · BarazArte", alternates: { canonical: "/legal/aviso-legal" } };

export default function AvisoLegal() {
  return (
    <LegalPage title="Aviso legal" updated="9 de noviembre de 2026" current="/legal/aviso-legal">
      <h2>Titular del sitio web</h2>
      <p>
        En cumplimiento del artículo 10 de la Ley 34/2002, de Servicios de la Sociedad de la Información y de Comercio
        Electrónico (LSSI-CE), se informa de que este sitio web, accesible en barazarte.klyp.es (en adelante,
        «BarazArte»), es titularidad de:
      </p>
      <ul>
        <li>Titular: <Fill>nombre y apellidos o razón social</Fill></li>
        <li>NIF/CIF: <Fill>NIF o CIF</Fill></li>
        <li>Domicilio: <Fill>dirección postal completa</Fill></li>
        <li>Email de contacto: <Fill>email de contacto</Fill></li>
        <li>Datos registrales (solo si es una sociedad): <Fill>Registro Mercantil, tomo, folio y hoja, o eliminar esta línea</Fill></li>
      </ul>

      <h2>Objeto</h2>
      <p>
        BarazArte es una galería online en la que artistas exponen sus obras originales. BarazArte no vende las obras ni
        interviene en el pago: facilita el contacto entre la persona interesada y el artista, que acuerdan directamente
        las condiciones de la compraventa (precio final, envío y forma de pago). Cada artista es responsable de la
        veracidad de la información de sus obras, de su autoría y de cumplir sus obligaciones fiscales y legales.
      </p>

      <h2>Condiciones de uso</h2>
      <p>
        El acceso a la web es gratuito. Quien la utiliza se compromete a hacerlo de forma lícita, a no introducir datos
        falsos ni de terceros sin su consentimiento y a no usar los formularios para enviar publicidad no solicitada.
        BarazArte puede retirar contenidos o deshabilitar cuentas de artistas que incumplan estas condiciones.
      </p>

      <h2>Propiedad intelectual</h2>
      <p>
        Las obras y sus fotografías pertenecen a sus respectivos artistas, que conservan todos los derechos de propiedad
        intelectual. No está permitido reproducirlas, distribuirlas ni utilizarlas con fines comerciales sin su
        autorización expresa. El diseño, el logotipo y los textos propios de BarazArte pertenecen a su titular.
      </p>

      <h2>Responsabilidad</h2>
      <p>
        BarazArte no se hace responsable de los acuerdos que alcancen compradores y artistas, ni del estado, la entrega o
        el pago de las obras. Tampoco de las interrupciones técnicas puntuales del servicio, aunque se procurará
        resolverlas con la mayor rapidez posible.
      </p>

      <h2>Legislación aplicable</h2>
      <p>
        Este aviso se rige por la legislación española. Para cualquier controversia serán competentes los juzgados y
        tribunales del domicilio del consumidor o, si no lo es, los de <Fill>ciudad del titular</Fill>.
      </p>
    </LegalPage>
  );
}
