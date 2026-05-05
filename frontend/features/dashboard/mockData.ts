import type { ApprovalSummary, DashboardItem, EvidenceSummary, WorkerSummary } from "../../types";

export const monthlyTasks: DashboardItem[] = [
  {
    id: "task-001",
    title: "E-9 신규 채용 요청 3건 검토",
    owner: "인사 담당자",
    dueLabel: "이번 주",
    status: "attention",
  },
  {
    id: "task-002",
    title: "체류기간 만료 전 서류 확인",
    owner: "비자 담당자",
    dueLabel: "D-21",
    status: "risk",
  },
  {
    id: "task-003",
    title: "다국어 서류 안내 메시지 승인",
    owner: "운영 매니저",
    dueLabel: "승인 대기",
    status: "approval",
  },
];

export const workersNearExpiry: WorkerSummary[] = [
  {
    id: "worker-001",
    displayName: "Ng***",
    visaType: "E-9",
    dDay: 21,
    documentStatus: "missing",
  },
  {
    id: "worker-002",
    displayName: "Tr***",
    visaType: "E-9",
    dDay: 34,
    documentStatus: "review",
  },
];

export const pendingApprovals: ApprovalSummary[] = [
  {
    id: "approval-001",
    actionType: "send_worker_message",
    target: "Ng*** 서류 요청 메시지",
    status: "PENDING",
    reason: "외국인 근로자에게 메시지를 보내기 전 담당자 승인이 필요합니다.",
  },
  {
    id: "approval-002",
    actionType: "export_handoff_package",
    target: "행정사 전달 패키지 초안",
    status: "PENDING",
    reason: "대외 전달용 export는 승인 후 진행해야 합니다.",
  },
];

export const recentEvidence: EvidenceSummary[] = [
  {
    id: "evidence-001",
    requestId: "req_001",
    actionType: "intent_classified",
    summary: "HIRING, VISA_CHECK 의도 감지",
    createdAt: "2026-05-05 13:30",
  },
  {
    id: "evidence-002",
    requestId: "req_001",
    actionType: "approval_requested",
    summary: "근로자 메시지 발송 승인 필요",
    createdAt: "2026-05-05 13:31",
  },
];
