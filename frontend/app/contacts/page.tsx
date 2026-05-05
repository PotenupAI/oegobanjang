import { pendingApprovals } from "../../features/dashboard/mockData";

export default function ContactsPage() {
  return (
    <section className="panel">
      <h1>다국어 메시지 초안</h1>
      {pendingApprovals.filter((approval) => approval.actionType.includes("message")).map((approval) => (
        <article className="listItem" key={approval.id}>
          <div>
            <strong>{approval.target}</strong>
            <span>{approval.reason}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
