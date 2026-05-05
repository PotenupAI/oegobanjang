import { workersNearExpiry } from "../../features/dashboard/mockData";

export default function VisaPage() {
  return (
    <section className="panel">
      <h1>비자 만료 관리</h1>
      {workersNearExpiry.map((worker) => (
        <article className="listItem" key={worker.id}>
          <div>
            <strong>{worker.displayName}</strong>
            <span>{worker.visaType} · D-{worker.dDay}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
