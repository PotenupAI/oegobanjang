export type DashboardItem = {
  id: string;
  title: string;
  owner: string;
  dueLabel: string;
  status: "normal" | "attention" | "approval" | "risk";
};

export type WorkerSummary = {
  id: string;
  displayName: string;
  visaType: string;
  dDay: number;
  documentStatus: "complete" | "missing" | "review";
};

export type ApprovalSummary = {
  id: string;
  actionType: string;
  target: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";
  reason: string;
};

export type EvidenceSummary = {
  id: string;
  requestId: string;
  actionType: string;
  summary: string;
  createdAt: string;
};
