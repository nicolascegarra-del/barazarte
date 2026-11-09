import { Suspense } from "react";
import { AuthCard } from "@/components/auth/AuthCard";
import { ConfirmReset } from "@/components/auth/PasswordForms";

export const metadata = { title: "Nueva contraseña · BarazArte", robots: { index: false, follow: false } };

export default function Restablecer() {
  return (
    <AuthCard title="Elige tu nueva contraseña">
      <Suspense fallback={<p className="text-sm text-muted">Cargando…</p>}>
        <ConfirmReset />
      </Suspense>
    </AuthCard>
  );
}
