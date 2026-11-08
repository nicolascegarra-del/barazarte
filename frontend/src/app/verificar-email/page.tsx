import { Suspense } from "react";
import { AuthCard } from "@/components/auth/AuthCard";
import { VerifyEmail } from "@/components/auth/VerifyEmail";

export const metadata = { title: "Verificar email · BarazArte" };

export default function VerificarEmail() {
  return (
    <AuthCard title="Verificar email">
      <Suspense fallback={<p className="text-sm text-muted">Cargando…</p>}>
        <VerifyEmail />
      </Suspense>
    </AuthCard>
  );
}
