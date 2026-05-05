import { workersNearExpiry } from "../../features/dashboard/mockData";

export default function WorkersPage() {
  return (
    <section className="panel">
      <h1>근로자</h1>
      {workersNearExpiry.map((worker) => (
        <article className="listItem" key={worker.id}>
          <div>
            <strong>{worker.displayName}</strong>
            <span>{worker.visaType} · D-{worker.dDay} · 서류 {worker.documentStatus}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
