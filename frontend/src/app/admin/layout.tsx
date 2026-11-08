import { PanelShell } from "@/components/panel/PanelShell";

export const metadata = { title: "Administración · BarazArte" };

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <PanelShell admin>{children}</PanelShell>;
}
