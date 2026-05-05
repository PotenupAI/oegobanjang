import { getApprovals } from "../../lib/api";
import { pendingApprovals as fallbackApprovals } from "../../features/dashboard/mockData";

export default async function ApprovalsPage() {
  let approvals = fallbackApprovals;
  let source = "mock fallback";
  try {
    const backendApprovals = await getApprovals();
    if (backendApprovals.length > 0) {
      approvals = backendApprovals;
    }
    source = "backend API";
  } catch {
    source = "mock fallback";
  }

  return (
    <section className="panel">
      <h1>승인 대기</h1>
      <p className="muted">데이터 소스: {source}. 실행 버튼 없이 승인 상태만 표시합니다.</p>
      {approvals.map((approval) => (
        <article className="listItem" key={approval.id}>
          <div>
            <strong>{approval.target}</strong>
            <span>{approval.status} · {approval.reason}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
