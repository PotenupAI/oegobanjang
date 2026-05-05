import { recentEvidence } from "../../features/dashboard/mockData";

export default function EvidencePage() {
  return (
    <section className="panel">
      <h1>Evidence Log</h1>
      {recentEvidence.map((event) => (
        <article className="listItem" key={event.id}>
          <div>
            <strong>{event.actionType}</strong>
            <span>{event.requestId} · {event.createdAt} · {event.summary}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
