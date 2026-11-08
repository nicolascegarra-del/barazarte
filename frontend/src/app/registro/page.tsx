import { AuthCard } from "@/components/auth/AuthCard";
import { RegisterForm } from "@/components/auth/RegisterForm";

export const metadata = { title: "Crear cuenta de artista · BarazArte" };

export default function Registro() {
  return (
    <AuthCard title="Crea tu cuenta de artista" intro="Sube tus obras y deja que los compradores contacten contigo.">
      <RegisterForm />
    </AuthCard>
  );
}
