import type { ReactNode } from "react";
import { APP_NAME, NAV_ITEMS } from "../lib/constants";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="appShell">
      <aside className="sidebar">
        <a className="brand" href="/dashboard">
          {APP_NAME}
        </a>
        <nav aria-label="주요 메뉴">
          {NAV_ITEMS.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>
      </aside>
      <main className="mainPanel">{children}</main>
    </div>
  );
}
