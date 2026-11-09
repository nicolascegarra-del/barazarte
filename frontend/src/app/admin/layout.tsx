import { PanelShell } from "@/components/panel/PanelShell";

export const metadata = { title: "Administración · BarazArte", robots: { index: false, follow: false } };

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <PanelShell admin>{children}</PanelShell>;
}
