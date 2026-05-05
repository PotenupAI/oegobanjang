import { getEvidenceEvents } from "../../lib/api";
import { recentEvidence as fallbackEvidence } from "../../features/dashboard/mockData";

export default async function EvidencePage() {
  let evidence = fallbackEvidence;
  let source = "mock fallback";
  try {
    const backendEvidence = await getEvidenceEvents();
    if (backendEvidence.length > 0) {
      evidence = backendEvidence;
    }
    source = "backend API";
  } catch {
    source = "mock fallback";
  }

  return (
    <section className="panel">
      <h1>Evidence Log</h1>
      <p className="muted">데이터 소스: {source}. request_id 기준 이력을 조회합니다.</p>
      {evidence.map((event) => (
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
