import { workersNearExpiry } from "../../features/dashboard/mockData";

export default function DocumentsPage() {
  return (
    <section className="panel">
      <h1>서류 누락 케이스</h1>
      {workersNearExpiry.filter((worker) => worker.documentStatus !== "complete").map((worker) => (
        <article className="listItem" key={worker.id}>
          <div>
            <strong>{worker.displayName}</strong>
            <span>서류 상태: {worker.documentStatus}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
