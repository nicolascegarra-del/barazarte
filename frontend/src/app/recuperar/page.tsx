import { AuthCard } from "@/components/auth/AuthCard";
import { RequestReset } from "@/components/auth/PasswordForms";

export const metadata = { title: "Recuperar contraseña · BarazArte", robots: { index: false, follow: false } };

export default function Recuperar() {
  return (
    <AuthCard title="Recuperar contraseña" intro="Te enviaremos un enlace para elegir una nueva.">
      <RequestReset />
    </AuthCard>
  );
}
