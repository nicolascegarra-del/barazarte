import { AuthCard } from "@/components/auth/AuthCard";
import { RegisterForm } from "@/components/auth/RegisterForm";

export const metadata = {
  title: "Expón y vende tus cuadros · BarazArte",
  description: "Crea gratis tu cuenta de artista en BarazArte, sube tus obras desde el móvil y recibe las consultas de compradores directamente.",
  alternates: { canonical: "/registro" },
};

export default function Registro() {
  return (
    <AuthCard title="Crea tu cuenta de artista" intro="Sube tus obras y deja que los compradores contacten contigo.">
      <RegisterForm />
    </AuthCard>
  );
}
