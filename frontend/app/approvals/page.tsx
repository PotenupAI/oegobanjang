import { pendingApprovals } from "../../features/dashboard/mockData";

export default function ApprovalsPage() {
  return (
    <section className="panel">
      <h1>승인 대기</h1>
      {pendingApprovals.map((approval) => (
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
