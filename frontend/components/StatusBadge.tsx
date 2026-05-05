import type { DashboardItem } from "../types";

const LABELS: Record<DashboardItem["status"], string> = {
  normal: "정상",
  attention: "확인",
  approval: "승인 필요",
  risk: "리스크",
};

export function StatusBadge({ status }: { status: DashboardItem["status"] }) {
  return <span className={`statusBadge status-${status}`}>{LABELS[status]}</span>;
}
