import type { ReactNode } from "react";
import { AppShell } from "../components/AppShell";
import "./styles.css";

export const metadata = {
  title: "외고반장 Dashboard",
  description: "외국인 고용 운영 OS 관리자 화면",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
