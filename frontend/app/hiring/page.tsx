import { monthlyTasks } from "../../features/dashboard/mockData";

export default function HiringPage() {
  return (
    <section className="panel">
      <h1>신규 채용 요청</h1>
      {monthlyTasks.filter((task) => task.title.includes("채용")).map((task) => (
        <article className="listItem" key={task.id}>
          <div>
            <strong>{task.title}</strong>
            <span>{task.owner} · {task.dueLabel}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
