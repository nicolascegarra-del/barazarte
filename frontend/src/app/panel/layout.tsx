import { PanelShell } from "@/components/panel/PanelShell";

export const metadata = { title: "Panel del artista · BarazArte", robots: { index: false, follow: false } };

export default function PanelLayout({ children }: { children: React.ReactNode }) {
  return <PanelShell>{children}</PanelShell>;
}
