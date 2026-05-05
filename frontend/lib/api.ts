import { API_BASE_URL } from "./constants";
import { monthlyTasks, pendingApprovals, recentEvidence, workersNearExpiry } from "../features/dashboard/mockData";
import type { AgentPreview, ApprovalSummary, DashboardData, EvidenceSummary } from "../types";

type ApiOptions = {
  requestId?: string;
  method?: "GET" | "POST";
  body?: unknown;
};

export async function fetchApi<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "content-type": "application/json",
      ...(options.requestId ? { "x-request-id": options.requestId } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

type ApprovalApiResponse = {
  approvals: Array<{
    approval_id: string;
    request_id: string;
    action_type: string;
    status: ApprovalSummary["status"];
    reason: string | null;
  }>;
};

type EvidenceApiResponse = {
  events: Array<{
    event_id: string;
    request_id: string;
    action_type: string;
    event_type: string;
    payload: Record<string, unknown>;
  }>;
};

type AgentRunResponse = {
  approval_required: boolean;
  final_response: {
    message?: string;
    status?: string;
  };
  evidence_events: Array<{
    action_type: string;
    event_type: string;
    work_item_id: string;
    timestamp: string;
  }>;
};

export async function getApprovals(): Promise<ApprovalSummary[]> {
  const response = await fetchApi<ApprovalApiResponse>("/approvals");
  return response.approvals
    .filter((approval) => approval.status === "PENDING")
    .map((approval) => ({
      id: approval.approval_id,
      actionType: approval.action_type,
      target: approval.request_id,
      status: approval.status,
      reason: approval.reason ?? "승인이 필요한 작업입니다.",
    }));
}

export async function getEvidenceEvents(requestId = "req_001"): Promise<EvidenceSummary[]> {
  const response = await fetchApi<EvidenceApiResponse>(`/evidence/${requestId}`);
  return response.events.map((event) => ({
    id: event.event_id,
    requestId: event.request_id,
    actionType: event.action_type || event.event_type,
    summary: event.event_type,
    createdAt: "backend",
  }));
}

export async function runAgentPreview(): Promise<AgentPreview> {
  const response = await fetchApi<AgentRunResponse>("/agent/run", {
    method: "POST",
    body: {
      request_id: "frontend_preview",
      user_message: "E-9 신규 채용 준비 상태를 확인해줘.",
      case_type: "new_hiring",
      input_state: {
        company_id: "company_001",
        requested_headcount: 3,
      },
    },
  });

  return {
    approvalRequired: response.approval_required,
    finalMessage: response.final_response.message ?? response.final_response.status ?? "응답이 생성되었습니다.",
    evidenceEvents: response.evidence_events.map((event) => ({
      id: `${event.work_item_id}-${event.event_type}`,
      requestId: event.work_item_id,
      actionType: event.action_type,
      summary: event.event_type,
      createdAt: event.timestamp,
    })),
  };
}

export async function getDashboardData(): Promise<DashboardData> {
  try {
    const [backendApprovals, agentPreview] = await Promise.all([
      getApprovals(),
      runAgentPreview(),
    ]);
    return {
      monthlyTasks,
      workersNearExpiry,
      pendingApprovals: backendApprovals.length > 0 ? backendApprovals : pendingApprovals,
      recentEvidence: agentPreview.evidenceEvents.length > 0 ? agentPreview.evidenceEvents : recentEvidence,
      source: "backend",
    };
  } catch (error) {
    return {
      monthlyTasks,
      workersNearExpiry,
      pendingApprovals,
      recentEvidence,
      source: "mock_fallback",
      error: error instanceof Error ? error.message : "API 연결 실패",
    };
  }
}
