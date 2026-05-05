export const APP_NAME = "외고반장";

export const NAV_ITEMS = [
  { href: "/dashboard", label: "대시보드" },
  { href: "/workers", label: "근로자" },
  { href: "/hiring", label: "채용" },
  { href: "/visa", label: "비자" },
  { href: "/documents", label: "서류" },
  { href: "/contacts", label: "메시지" },
  { href: "/approvals", label: "승인" },
  { href: "/evidence", label: "Evidence" },
] as const;

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
