import { StatusBadge } from "../../components/StatusBadge";
import { monthlyTasks, pendingApprovals, recentEvidence, workersNearExpiry } from "../../features/dashboard/mockData";

export default function DashboardPage() {
  return (
    <>
      <section className="pageHeader">
        <p className="eyebrow">관리자 대시보드</p>
        <h1>승인, 기한, 누락 서류를 한 화면에서 봅니다.</h1>
      </section>

      <section className="metricGrid" aria-label="업무 요약">
        <article>
          <strong>{monthlyTasks.length}</strong>
          <span>이번 달 처리 업무</span>
        </article>
        <article>
          <strong>{workersNearExpiry.length}</strong>
          <span>비자 만료 임박</span>
        </article>
        <article>
          <strong>{pendingApprovals.length}</strong>
          <span>승인 대기</span>
        </article>
      </section>

      <section className="contentGrid">
        <div className="panel">
          <h2>이번 달 처리 필요 업무</h2>
          {monthlyTasks.map((task) => (
            <article className="listItem" key={task.id}>
              <div>
                <strong>{task.title}</strong>
                <span>{task.owner} · {task.dueLabel}</span>
              </div>
              <StatusBadge status={task.status} />
            </article>
          ))}
        </div>

        <div className="panel">
          <h2>비자 만료 임박 근로자</h2>
          {workersNearExpiry.map((worker) => (
            <article className="listItem" key={worker.id}>
              <div>
                <strong>{worker.displayName} · {worker.visaType}</strong>
                <span>D-{worker.dDay} · 서류 {worker.documentStatus}</span>
              </div>
            </article>
          ))}
        </div>

        <div className="panel">
          <h2>승인 대기 작업</h2>
          {pendingApprovals.map((approval) => (
            <article className="listItem" key={approval.id}>
              <div>
                <strong>{approval.target}</strong>
                <span>{approval.actionType} · {approval.status}</span>
              </div>
            </article>
          ))}
        </div>

        <div className="panel">
          <h2>Evidence Log 최근 이력</h2>
          {recentEvidence.map((event) => (
            <article className="listItem" key={event.id}>
              <div>
                <strong>{event.actionType}</strong>
                <span>{event.requestId} · {event.summary}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
